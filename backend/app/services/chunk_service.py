from typing import List
import re


def detectar_seccion(texto: str) -> str:
    """
    Detecta la sección del pliego basándose en palabras clave y patrones.

    Args:
        texto: Fragmento de texto a analizar

    Returns:
        Nombre de la sección detectada
    """
    texto_upper = texto.upper()

    # Patrones de secciones comunes en pliegos colombianos
    patrones_secciones = [
        (r'CAP[IÍ]TULO\s+([IVXLCDM\d]+|[A-Z]+)[\s\.:]+(.+?)(?:\n|$)', 'capítulo'),
        (r'OBJETO\s*:', 'objeto'),
        (r'PRESUPUESTO\s*:', 'presupuesto'),
        (r'CRONOGRAMA\s*:', 'cronograma'),
        (r'REQUISITOS?\s+HABILITANTES?', 'requisitos_habilitantes'),
        (r'REQUISITOS?\s+T[EÉ]CNICOS?', 'requisitos_tecnicos'),
        (r'EXPERIENCIA\s+REQUERIDA', 'experiencia'),
        (r'CRITERIOS?\s+DE\s+EVALUACI[OÓ]N', 'criterios_evaluacion'),
        (r'GARANT[IÍ]AS?', 'garantias'),
        (r'CONDICIONES?\s+CONTRACTUALES?', 'condiciones_contractuales'),
        (r'PLAZO\s+DE\s+EJECUCI[OÓ]N', 'plazo'),
        (r'OBLIGACIONES?\s+DEL\s+CONTRATISTA', 'obligaciones'),
        (r'FORMA\s+DE\s+PAGO', 'forma_pago'),
        (r'^\s*(\d+\.)+\d*\s+([A-Z\u00c1\u00c9\u00cd\u00d3\u00da\u00d1][A-Z\u00c1\u00c9\u00cd\u00d3\u00da\u00d1\s]{3,})', 'numeración'),
    ]

    for patron, nombre_seccion in patrones_secciones:
        match = re.search(patron, texto_upper[:500])  # Buscar en los primeros 500 caracteres
        if match:
            if nombre_seccion == 'capítulo' or nombre_seccion == 'numeración':
                # Retornar el texto completo del match para mayor contexto
                return match.group(0).strip()
            return nombre_seccion

    return "sin_seccion"


def encontrar_pagina_chunk(posicion_palabra: int, paginas: List[dict]) -> int:
    """
    Encuentra el número de página basándose en la posición de palabra.

    Args:
        posicion_palabra: Posición de la palabra en el documento completo
        paginas: Lista de dicts con numero y texto de cada página

    Returns:
        Número de página (1-indexed)
    """
    if not paginas:
        return 1

    palabras_acumuladas = 0
    for pagina in paginas:
        palabras_en_pagina = len(pagina["texto"].split())
        if posicion_palabra < palabras_acumuladas + palabras_en_pagina:
            return pagina["numero"]
        palabras_acumuladas += palabras_en_pagina

    # Si no se encuentra, retornar la última página
    return paginas[-1]["numero"] if paginas else 1


def dividir_en_chunks(texto: str, paginas: List[dict] = None, tamano: int = 500, solapamiento: int = 50) -> List[dict]:
    """
    Divide texto en chunks con solapamiento, detectando página y sección.

    Args:
        texto: Texto completo del documento
        paginas: Lista de dicts con numero y texto de cada página
        tamano: Palabras por chunk (aprox)
        solapamiento: Palabras que se repiten entre chunks

    Returns:
        Lista de dicts con texto, metadata, page y section
    """
    palabras = texto.split()
    chunks = []
    inicio = 0
    chunk_id = 0

    while inicio < len(palabras):
        fin = inicio + tamano
        chunk_texto = " ".join(palabras[inicio:fin])

        # Detectar página
        pagina = encontrar_pagina_chunk(inicio, paginas) if paginas else 1

        # Detectar sección
        seccion = detectar_seccion(chunk_texto)

        chunks.append({
            "id": chunk_id,
            "texto": chunk_texto,
            "inicio": inicio,
            "fin": min(fin, len(palabras)),
            "palabras": len(chunk_texto.split()),
            "page": pagina,
            "section": seccion
        })

        chunk_id += 1
        inicio = fin - solapamiento

        if fin >= len(palabras):
            break

    return chunks
