from app.services.pdf_service import extraer_texto_pdf
from app.services.ollama_service import preguntar_ollama, generar_resumen
from app.services.chunk_service import dividir_en_chunks
from app.services.embedding_service import (
    guardar_chunks,
    buscar_chunks_relevantes,
    buscar_normativa,
    eliminar_chunks_pliego
)
