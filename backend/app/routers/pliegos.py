import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Pliego
from app.schemas import PliegoResponse, PliegoDetalle, ChecklistRequest, ChecklistResponse
from app.services import extraer_texto_pdf, dividir_en_chunks, guardar_chunks, eliminar_chunks_pliego, generar_checklist_completo

router = APIRouter(prefix="/api/pliegos", tags=["pliegos"])

UPLOAD_DIR = "/app/uploads"


@router.post("/upload", response_model=PliegoResponse)
async def subir_pliego(
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Sube un PDF, extrae texto y genera chunks."""
    
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

        # Generar chunks y guardar en ChromaDB
        try:
            chunks = dividir_en_chunks(
                texto=resultado["texto_completo"],
                paginas=resultado.get("paginas", [])
            )
            guardar_chunks(pliego.id, chunks)
            pliego.texto_tokens = len(resultado["texto_completo"].split())
            pliego.estado = "listo"
        except Exception as e:
            pliego.estado = "error"
            pliego.error_mensaje = f"Error al generar chunks: {str(e)}"

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
    """Elimina un pliego, su archivo y sus chunks."""
    pliego = db.query(Pliego).filter(Pliego.id == pliego_id).first()
    if not pliego:
        raise HTTPException(status_code=404, detail="Pliego no encontrado")

    # Eliminar archivo físico
    if os.path.exists(pliego.ruta_archivo):
        os.remove(pliego.ruta_archivo)

    # Eliminar chunks de ChromaDB
    try:
        eliminar_chunks_pliego(pliego_id)
    except:
        pass

    # Eliminar de BD
    db.delete(pliego)
    db.commit()

    return {"mensaje": "Pliego eliminado"}


@router.post("/checklist", response_model=ChecklistResponse)
def generar_checklist_documentos(
    datos: ChecklistRequest,
    db: Session = Depends(get_db)
):
    """Genera checklist de documentos requeridos: base + detectados por IA."""

    pliego = db.query(Pliego).filter(Pliego.id == datos.pliego_id).first()
    if not pliego:
        raise HTTPException(status_code=404, detail="Pliego no encontrado")

    if pliego.estado != "listo":
        raise HTTPException(status_code=400, detail="El pliego aún no está procesado")

    if not pliego.texto_completo:
        raise HTTPException(status_code=400, detail="El pliego no tiene texto extraído")

    # Generar checklist
    resultado = generar_checklist_completo(pliego.id, pliego.texto_completo)

    if resultado.get("error"):
        # Aunque haya error, retornar lo que se pudo generar
        pass

    # Guardar checklist en el pliego
    import json
    pliego.checklist_documentos = json.dumps(resultado, ensure_ascii=False)
    db.commit()

    return ChecklistResponse(
        documentos_base=resultado["documentos_base"],
        documentos_especificos=resultado["documentos_especificos"],
        total_documentos=resultado["total_documentos"]
    )
