import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Pliego
from app.schemas import PliegoResponse, PliegoDetalle
from app.services import extraer_texto_pdf

router = APIRouter(prefix="/api/pliegos", tags=["pliegos"])

UPLOAD_DIR = "/app/uploads"


@router.post("/upload", response_model=PliegoResponse)
async def subir_pliego(
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Sube un PDF y extrae su texto."""
    
    if not archivo.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF")

    # Crear nombre único
    nombre_unico = f"{uuid.uuid4()}_{archivo.filename}"
    ruta_completa = os.path.join(UPLOAD_DIR, nombre_unico)

    # Guardar archivo
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    contenido = await archivo.read()
    with open(ruta_completa, "wb") as f:
        f.write(contenido)

    # Crear registro en BD
    pliego = Pliego(
        nombre_archivo=archivo.filename,
        ruta_archivo=ruta_completa,
        tamano_bytes=len(contenido),
        estado="procesando"
    )
    db.add(pliego)
    db.commit()
    db.refresh(pliego)

    # Extraer texto
    resultado = extraer_texto_pdf(ruta_completa)

    if resultado["error"]:
        pliego.estado = "error"
        pliego.error_mensaje = resultado["error"]
    else:
        pliego.texto_completo = resultado["texto_completo"]
        pliego.num_paginas = resultado["num_paginas"]
        pliego.estado = "listo"

    db.commit()
    db.refresh(pliego)

    return pliego


@router.get("", response_model=List[PliegoResponse])
def listar_pliegos(db: Session = Depends(get_db)):
    """Lista todos los pliegos."""
    return db.query(Pliego).order_by(Pliego.created_at.desc()).all()


@router.get("/{pliego_id}", response_model=PliegoDetalle)
def obtener_pliego(pliego_id: int, db: Session = Depends(get_db)):
    """Obtiene detalle de un pliego específico."""
    pliego = db.query(Pliego).filter(Pliego.id == pliego_id).first()
    if not pliego:
        raise HTTPException(status_code=404, detail="Pliego no encontrado")
    return pliego


@router.delete("/{pliego_id}")
def eliminar_pliego(pliego_id: int, db: Session = Depends(get_db)):
    """Elimina un pliego y su archivo."""
    pliego = db.query(Pliego).filter(Pliego.id == pliego_id).first()
    if not pliego:
        raise HTTPException(status_code=404, detail="Pliego no encontrado")

    # Eliminar archivo físico
    if os.path.exists(pliego.ruta_archivo):
        os.remove(pliego.ruta_archivo)

    # Eliminar de BD
    db.delete(pliego)
    db.commit()

    return {"mensaje": "Pliego eliminado"}