from fastapi import FastAPI, Depends, BackgroundTasks, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import joblib
import logging
import os
import random
import re
from dotenv import load_dotenv

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import database
from database import Tramite, Funcionario, SessionLocal
from jose import JWTError, jwt
import auth
from auth import create_access_token, verify_password, get_password_hash, SECRET_KEY, ALGORITHM

# Cargar variables de entorno
load_dotenv()
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
SMTP_USER = os.getenv("SMTP_USER", "default@gmail.com")

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurar Limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="API Municipalidad de Yau - MVP")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Intentar cargar el modelo al iniciar
try:
    modelo_tramites = joblib.load("modelo_tramites.pkl")
    logger.info("Modelo ML cargado correctamente.")
except FileNotFoundError:
    logger.warning("No se encontró 'modelo_tramites.pkl'. Asegúrate de entrenar el modelo primero.")
    modelo_tramites = None

# Dependencia para la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.on_event("startup")
def startup_event():
    # Crear administrador por defecto si no existe
    db = SessionLocal()
    admin_user = os.getenv("ADMIN_USER", "admin")
    admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")
    
    usuario = db.query(Funcionario).filter(Funcionario.username == admin_user).first()
    if not usuario:
        nuevo_admin = Funcionario(
            username=admin_user,
            hashed_password=get_password_hash(admin_pass)
        )
        db.add(nuevo_admin)
        db.commit()
    db.close()
    logger.info("Verificación de Administrador completada.")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o token expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(Funcionario).filter(Funcionario.username == username).first()
    if user is None:
        raise credentials_exception
    return user

@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(Funcionario).filter(Funcionario.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# Pydantic models para la API con validaciones de estrés
class TramiteCreate(BaseModel):
    dni: str = Field(..., min_length=8, max_length=15, description="Documento de Identidad")
    nombres: str = Field(..., min_length=3, max_length=100, description="Nombre Completo")
    email: str = Field(..., min_length=5, max_length=100, description="Correo Electrónico")
    descripcion: str = Field(..., min_length=10, max_length=1500, description="Descripción del trámite o incidente")

class TramiteResponse(BaseModel):
    id: int
    dni: str
    nombres: str
    descripcion: str
    prioridad: str
    estado: str
    
    class Config:
        from_attributes = True

# Filtro Heurístico
def es_spam_heuristico(texto: str) -> bool:
    texto = texto.lower()
    # Demasiadas consonantes seguidas (ej. "fhjksdhfks")
    if re.search(r'[bcdfghjklmnpqrstvwxyz]{6,}', texto):
        return True
    # Texto repetitivo o risas
    if "jajaja" in texto or "asdasd" in texto or "qweqwe" in texto:
        return True
    return False

# Simular envío de correo electrónico (Fase 4)
def enviar_correo_simulado(email: str, id_tramite: int, prioridad: str, estado: str):
    logger.info("*"*50)
    logger.info(f"SIMULACIÓN DE ENVÍO DE CORREO SMTP (Usando {SMTP_USER})")
    logger.info(f"Para: {email}")
    logger.info(f"Asunto: Actualización de Trámite N° {id_tramite}")
    logger.info(f"Mensaje: Su trámite ha sido recibido y catalogado con Prioridad {prioridad}. Estado actual: {estado}.")
    logger.info("*"*50)

@app.post("/tramites/nuevo", response_model=TramiteResponse)
@limiter.limit("3/minute")
def crear_tramite(request: Request, tramite: TramiteCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    
    # 1. Filtro Heurístico (Anti-Troll)
    if es_spam_heuristico(tramite.descripcion) or es_spam_heuristico(tramite.nombres):
        logger.warning(f"Spam detectado y descartado silenciosamente: {tramite.descripcion}")
        # Retornar ID falso sin tocar la DB (Shadow Banning perfecto)
        fake_id = random.randint(90000, 99999)
        return TramiteResponse(
            id=fake_id,
            dni=tramite.dni,
            nombres=tramite.nombres,
            descripcion=tramite.descripcion,
            prioridad="Baja",
            estado="En Evaluación"
        )
    
    # 2. Predecir prioridad usando el modelo de ML
    prioridad = "Media" # Por defecto
    if modelo_tramites:
        prediccion = modelo_tramites.predict([tramite.descripcion])
        prioridad = prediccion[0]
        
    # 3. Guardar en base de datos
    nuevo_tramite = Tramite(
        dni=tramite.dni,
        nombres=tramite.nombres,
        email=tramite.email,
        descripcion=tramite.descripcion,
        prioridad=prioridad
    )
    db.add(nuevo_tramite)
    db.commit()
    db.refresh(nuevo_tramite)
    
    # 4. Lanzar alerta en background (Fase 4)
    background_tasks.add_task(
        enviar_correo_simulado, 
        email=nuevo_tramite.email, 
        id_tramite=nuevo_tramite.id, 
        prioridad=nuevo_tramite.prioridad, 
        estado=nuevo_tramite.estado
    )
    
    return nuevo_tramite

@app.get("/tramites", response_model=list[TramiteResponse])
def listar_tramites(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: Funcionario = Depends(get_current_user)):
    tramites = db.query(Tramite).offset(skip).limit(limit).all()
    return tramites
