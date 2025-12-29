from typing import List

def dividir_en_chunks(texto: str, tamano: int = 500, solapamiento: int = 50) -> List[dict]:
    """
    Divide texto en chunks con solapamiento.
    
    Args:
        texto: Texto completo del documento
        tamano: Palabras por chunk (aprox)
        solapamiento: Palabras que se repiten entre chunks
    
    Returns:
        Lista de dicts con texto y metadata
    """
    palabras = texto.split()
    chunks = []
    inicio = 0
    chunk_id = 0
    
    while inicio < len(palabras):
        fin = inicio + tamano
        chunk_texto = " ".join(palabras[inicio:fin])
        
        chunks.append({
            "id": chunk_id,
            "texto": chunk_texto,
            "inicio": inicio,
            "fin": min(fin, len(palabras)),
            "palabras": len(chunk_texto.split())
        })
        
        chunk_id += 1
        inicio = fin - solapamiento
        
        if fin >= len(palabras):
            break
    
    return chunks
