from fastapi import FastAPI, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import joblib
import logging
import os
from dotenv import load_dotenv

import database
from database import Tramite, SessionLocal

# Cargar variables de entorno
load_dotenv()
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
SMTP_USER = os.getenv("SMTP_USER", "default@gmail.com")

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="API Municipalidad de Yau - MVP")

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

# Simular envío de correo electrónico (Fase 4)
def enviar_correo_simulado(email: str, id_tramite: int, prioridad: str, estado: str):
    logger.info("*"*50)
    logger.info(f"SIMULACIÓN DE ENVÍO DE CORREO SMTP (Usando {SMTP_USER})")
    logger.info(f"Para: {email}")
    logger.info(f"Asunto: Actualización de Trámite N° {id_tramite}")
    logger.info(f"Mensaje: Su trámite ha sido recibido y catalogado con Prioridad {prioridad}. Estado actual: {estado}.")
    logger.info("*"*50)

@app.post("/tramites/nuevo", response_model=TramiteResponse)
def crear_tramite(tramite: TramiteCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # 1. Predecir prioridad usando el modelo de ML
    prioridad = "Media" # Por defecto
    if modelo_tramites:
        # El modelo espera una lista de strings
        prediccion = modelo_tramites.predict([tramite.descripcion])
        prioridad = prediccion[0]
        
    # 2. Guardar en base de datos
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
    
    # 3. Lanzar alerta en background (Fase 4)
    background_tasks.add_task(
        enviar_correo_simulado, 
        email=nuevo_tramite.email, 
        id_tramite=nuevo_tramite.id, 
        prioridad=nuevo_tramite.prioridad, 
        estado=nuevo_tramite.estado
    )
    
    return nuevo_tramite

@app.get("/tramites", response_model=list[TramiteResponse])
def listar_tramites(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    tramites = db.query(Tramite).offset(skip).limit(limit).all()
    return tramites
