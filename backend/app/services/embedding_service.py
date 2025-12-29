import chromadb
from sentence_transformers import SentenceTransformer
from typing import List
import os

# Inicializar modelo de embeddings

# Inicializar modelo de embeddings (se carga al importar)
from sentence_transformers import SentenceTransformer
modelo_embeddings = SentenceTransformer('all-MiniLM-L6-v2')

cliente_chroma = None
coleccion_pliegos = None
coleccion_normativa = None

def inicializar_servicios():
    """Inicializa modelo de embeddings y ChromaDB."""
    global modelo_embeddings, cliente_chroma, coleccion_pliegos, coleccion_normativa
    
    if cliente_chroma is None:
        ruta_db = os.environ.get('CHROMA_PATH', '/app/chroma_data')
        cliente_chroma = chromadb.PersistentClient(path=ruta_db)
        
        coleccion_pliegos = cliente_chroma.get_or_create_collection(
            name="pliegos",
            metadata={"descripcion": "Chunks de pliegos de usuarios"}
        )
        
        coleccion_normativa = cliente_chroma.get_or_create_collection(
            name="normativa",
            metadata={"descripcion": "Normativa colombiana de contratacion"}
        )

def guardar_chunks(pliego_id: int, chunks: List[dict]):
    """Guarda chunks de un pliego en ChromaDB."""
    inicializar_servicios()
    
    textos = [c["texto"] for c in chunks]
    ids = [f"pliego_{pliego_id}_chunk_{c['id']}" for c in chunks]
    metadatas = [{"pliego_id": pliego_id, "chunk_id": c["id"]} for c in chunks]
    
    embeddings = modelo_embeddings.encode(textos).tolist()
    
    coleccion_pliegos.add(
        documents=textos,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas
    )

def buscar_chunks_relevantes(pregunta: str, pliego_id: int, n_resultados: int = 5) -> List[str]:
    """Busca chunks relevantes para una pregunta."""
    inicializar_servicios()
    
    embedding_pregunta = modelo_embeddings.encode([pregunta]).tolist()
    
    resultados = coleccion_pliegos.query(
        query_embeddings=embedding_pregunta,
        n_results=n_resultados,
        where={"pliego_id": pliego_id}
    )
    
    return resultados["documents"][0] if resultados["documents"] else []

def buscar_normativa(pregunta: str, n_resultados: int = 3) -> List[str]:
    """Busca normativa relevante para una pregunta."""
    inicializar_servicios()
    
    embedding_pregunta = modelo_embeddings.encode([pregunta]).tolist()
    
    resultados = coleccion_normativa.query(
        query_embeddings=embedding_pregunta,
        n_results=n_resultados
    )
    
    return resultados["documents"][0] if resultados["documents"] else []

def eliminar_chunks_pliego(pliego_id: int):
    """Elimina todos los chunks de un pliego."""
    inicializar_servicios()
    
    coleccion_pliegos.delete(
        where={"pliego_id": pliego_id}
    )
