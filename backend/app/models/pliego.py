from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Pliego(Base):
    __tablename__ = "pliegos"

    id = Column(Integer, primary_key=True, index=True)
    numero_proceso = Column(String(100), index=True)
    entidad = Column(String(255))
    objeto = Column(Text)
    nombre_archivo = Column(String(255), nullable=False)
    ruta_archivo = Column(String(500), nullable=False)
    tamano_bytes = Column(Integer)
    num_paginas = Column(Integer)
    texto_completo = Column(Text)
    texto_tokens = Column(Integer)
    datos_extraidos = Column(JSON)
    checklist_documentos = Column(JSON)
    estado = Column(
        Enum("procesando", "listo", "error", name="estado_pliego"),
        default="procesando"
    )
    error_mensaje = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    conversaciones = relationship("Conversacion", back_populates="pliego", cascade="all, delete-orphan")


class Conversacion(Base):
    __tablename__ = "conversaciones"

    id = Column(Integer, primary_key=True, index=True)
    pliego_id = Column(Integer, ForeignKey("pliegos.id", ondelete="CASCADE"), nullable=False)
    pregunta = Column(Text, nullable=False)
    respuesta = Column(Text)
    modelo_usado = Column(String(100))
    tokens_prompt = Column(Integer)
    tokens_respuesta = Column(Integer)
    tiempo_respuesta_ms = Column(Integer)
    fue_util = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())

    pliego = relationship("Pliego", back_populates="conversaciones")