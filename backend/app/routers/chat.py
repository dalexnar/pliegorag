from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Pliego, Conversacion
from app.schemas import (
    PreguntaRequest,
    RespuestaChat,
    ConversacionResponse,
    ResumenRequest,
    ResumenResponse,
)
from app.services import preguntar_ollama, generar_resumen

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/preguntar", response_model=RespuestaChat)
def hacer_pregunta(
    datos: PreguntaRequest,
    db: Session = Depends(get_db)
):
    """Hace una pregunta sobre un pliego usando Ollama."""

    pliego = db.query(Pliego).filter(Pliego.id == datos.pliego_id).first()
    if not pliego:
        raise HTTPException(status_code=404, detail="Pliego no encontrado")

    if pliego.estado != "listo":
        raise HTTPException(status_code=400, detail="El pliego aún no está procesado")

    if not pliego.texto_completo:
        raise HTTPException(status_code=400, detail="El pliego no tiene texto extraído")

    # Preguntar a Ollama
    resultado = preguntar_ollama(pliego.texto_completo, datos.pregunta)

    if resultado["error"]:
        raise HTTPException(status_code=500, detail=resultado["error"])

    # Guardar conversación
    conversacion = Conversacion(
        pliego_id=pliego.id,
        pregunta=datos.pregunta,
        respuesta=resultado["respuesta"],
        modelo_usado="llama3.1:latest",
        tokens_prompt=resultado["tokens_prompt"],
        tokens_respuesta=resultado["tokens_respuesta"],
        tiempo_respuesta_ms=resultado["tiempo_ms"]
    )
    db.add(conversacion)
    db.commit()

    return RespuestaChat(
        respuesta=resultado["respuesta"],
        tokens_prompt=resultado["tokens_prompt"],
        tokens_respuesta=resultado["tokens_respuesta"],
        tiempo_ms=resultado["tiempo_ms"]
    )


@router.get("/historial/{pliego_id}", response_model=List[ConversacionResponse])
def obtener_historial(pliego_id: int, db: Session = Depends(get_db)):
    """Obtiene el historial de preguntas de un pliego."""

    pliego = db.query(Pliego).filter(Pliego.id == pliego_id).first()
    if not pliego:
        raise HTTPException(status_code=404, detail="Pliego no encontrado")

    conversaciones = (
        db.query(Conversacion)
        .filter(Conversacion.pliego_id == pliego_id)
        .order_by(Conversacion.created_at.desc())
        .all()
    )

    return conversaciones


@router.post("/resumen", response_model=ResumenResponse)
def crear_resumen(
    datos: ResumenRequest,
    db: Session = Depends(get_db)
):
    """Genera una ficha resumen automática del pliego."""

    pliego = db.query(Pliego).filter(Pliego.id == datos.pliego_id).first()
    if not pliego:
        raise HTTPException(status_code=404, detail="Pliego no encontrado")

    if pliego.estado != "listo":
        raise HTTPException(status_code=400, detail="El pliego aún no está procesado")

    if not pliego.texto_completo:
        raise HTTPException(status_code=400, detail="El pliego no tiene texto extraído")

    resultado = generar_resumen(pliego.texto_completo)

    if resultado["error"]:
        raise HTTPException(status_code=500, detail=resultado["error"])

    # Guardar datos extraídos en el pliego
    pliego.datos_extraidos = resultado["ficha"]
    db.commit()

    return ResumenResponse(ficha=resultado["ficha"])