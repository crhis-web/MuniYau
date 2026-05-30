from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./municipalidad.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Tramite(Base):
    __tablename__ = "tramites"

    id = Column(Integer, primary_key=True, index=True)
    dni = Column(String, index=True)
    nombres = Column(String)
    email = Column(String)
    descripcion = Column(String)
    prioridad = Column(String) # Alta, Media, Baja
    estado = Column(String, default="En Evaluación")
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)

# Crear las tablas
Base.metadata.create_all(bind=engine)
