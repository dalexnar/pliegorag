import pdfplumber
from pathlib import Path


def extraer_texto_pdf(ruta_archivo: str) -> dict:
    """
    Extrae texto de un archivo PDF.
    Retorna dict con texto_completo, num_paginas, y error si hay.
    """
    resultado = {
        "texto_completo": "",
        "num_paginas": 0,
        "error": None
    }

    try:
        ruta = Path(ruta_archivo)
        if not ruta.exists():
            resultado["error"] = f"Archivo no encontrado: {ruta_archivo}"
            return resultado

        with pdfplumber.open(ruta) as pdf:
            resultado["num_paginas"] = len(pdf.pages)
            textos = []

            for pagina in pdf.pages:
                texto = pagina.extract_text()
                if texto:
                    textos.append(texto)

            resultado["texto_completo"] = "\n\n".join(textos)

    except Exception as e:
        resultado["error"] = str(e)

    return resultado