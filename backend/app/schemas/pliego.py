from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# === PLIEGOS ===

class PliegoBase(BaseModel):
    numero_proceso: Optional[str] = None
    entidad: Optional[str] = None
    objeto: Optional[str] = None


class PliegoCreate(PliegoBase):
    pass


class PliegoResponse(PliegoBase):
    id: int
    nombre_archivo: str
    estado: str
    num_paginas: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PliegoDetalle(PliegoResponse):
    texto_completo: Optional[str] = None
    datos_extraidos: Optional[dict] = None
    error_mensaje: Optional[str] = None


# === CHAT ===

class PreguntaRequest(BaseModel):
    pliego_id: int
    pregunta: str


class RespuestaChat(BaseModel):
    respuesta: str
    tokens_prompt: Optional[int] = None
    tokens_respuesta: Optional[int] = None
    tiempo_ms: Optional[int] = None


class ConversacionResponse(BaseModel):
    id: int
    pregunta: str
    respuesta: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# === RESUMEN ===

class ResumenRequest(BaseModel):
    pliego_id: int


class ResumenResponse(BaseModel):
    ficha: dict