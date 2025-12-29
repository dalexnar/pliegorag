from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


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


class FuenteChunk(BaseModel):
    page: int
    section: str


class RespuestaChat(BaseModel):
    respuesta: str
    tokens_prompt: Optional[int] = None
    tokens_respuesta: Optional[int] = None
    tiempo_ms: Optional[int] = None
    fuentes: Optional[list[FuenteChunk]] = []


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


# === CHECKLIST DE DOCUMENTOS ===

class ReferenciaDocumento(BaseModel):
    page: int
    section: str
    extracto: Optional[str] = None


class DocumentoRequerido(BaseModel):
    nombre: str
    descripcion: str
    categoria: str
    siempre_requerido: bool = False
    referencias: List[ReferenciaDocumento] = []


class ChecklistRequest(BaseModel):
    pliego_id: int


class ChecklistResponse(BaseModel):
    documentos_base: List[DocumentoRequerido]
    documentos_especificos: List[DocumentoRequerido]
    total_documentos: int