import httpx
import time
from app.config import settings
from app.services.embedding_service import buscar_chunks_relevantes, buscar_normativa

MODELO_SIMPLE = "llama3.2:latest"
MODELO_COMPLEJO = "llama3.1:latest"

def es_pregunta_simple(pregunta: str) -> bool:
    """Detecta si es pregunta simple o necesita análisis."""
    palabras_simples = [
        "qué es", "que es", "definición", "definicion",
        "significa", "concepto", "explica", "explicame"
    ]
    pregunta_lower = pregunta.lower()
    return any(p in pregunta_lower for p in palabras_simples)

def preguntar_ollama(pliego_id: int, pregunta: str, texto_completo: str = None) -> dict:
    """Envía pregunta a Ollama usando chunks relevantes."""
    resultado = {
        "respuesta": "",
        "tokens_prompt": 0,
        "tokens_respuesta": 0,
        "tiempo_ms": 0,
        "modelo_usado": "",
        "error": None
    }

    try:
        if es_pregunta_simple(pregunta):
            modelo = MODELO_SIMPLE
            contexto = ""
        else:
            modelo = MODELO_COMPLEJO
            chunks = buscar_chunks_relevantes(pregunta, pliego_id, n_resultados=3)
            normativa = buscar_normativa(pregunta, n_resultados=2)
            
            contexto_pliego = "\n\n".join([c[:1000] for c in chunks]) if chunks else texto_completo[:3000] if texto_completo else ""
            contexto_legal = "\n\n".join(normativa) if normativa else ""
            
            if contexto_legal:
                contexto = f"EXTRACTOS DEL PLIEGO:\n{contexto_pliego}\n\nNORMATIVA APLICABLE:\n{contexto_legal}"
            else:
                contexto = f"EXTRACTOS DEL PLIEGO:\n{contexto_pliego}"

        resultado["modelo_usado"] = modelo

        prompt = f"""Eres un experto en contratación estatal colombiana.
Analiza la información y responde la pregunta del usuario.

{contexto}

PREGUNTA: {pregunta}

Responde de forma clara y concisa."""

        inicio = time.time()

        with httpx.Client(timeout=300.0) as client:
            response = client.post(
                f"{settings.OLLAMA_HOST}/api/generate",
                json={"model": modelo, "prompt": prompt, "stream": False}
            )
            response.raise_for_status()
            data = response.json()

        fin = time.time()

        resultado["respuesta"] = data.get("response", "")
        resultado["tokens_prompt"] = data.get("prompt_eval_count", 0)
        resultado["tokens_respuesta"] = data.get("eval_count", 0)
        resultado["tiempo_ms"] = int((fin - inicio) * 1000)

    except httpx.TimeoutException:
        resultado["error"] = "Timeout: Ollama tardó demasiado en responder"
    except httpx.HTTPError as e:
        resultado["error"] = f"Error HTTP: {str(e)}"
    except Exception as e:
        resultado["error"] = f"Error: {str(e)}"

    return resultado


def generar_resumen(texto_pliego: str) -> dict:
    """Genera ficha resumen estructurada del pliego."""
    resultado = {"ficha": {}, "error": None}

    prompt = f"""Eres un experto en contratación estatal colombiana.
Analiza el siguiente pliego y extrae la información clave.

PLIEGO:
{texto_pliego[:10000]}

Responde ÚNICAMENTE con un JSON válido:
{{
    "numero_proceso": "número del proceso",
    "entidad": "nombre de la entidad",
    "objeto": "objeto del contrato",
    "presupuesto": "presupuesto oficial",
    "fecha_cierre": "fecha límite",
    "experiencia_requerida": "requisitos de experiencia",
    "garantias": "garantías solicitadas",
    "criterios_evaluacion": "criterios y ponderación",
    "observaciones": "puntos importantes"
}}"""

    try:
        with httpx.Client(timeout=300.0) as client:
            response = client.post(
                f"{settings.OLLAMA_HOST}/api/generate",
                json={"model": MODELO_COMPLEJO, "prompt": prompt, "stream": False}
            )
            response.raise_for_status()
            data = response.json()

        import json
        respuesta_texto = data.get("response", "{}")
        resultado["ficha"] = json.loads(respuesta_texto)

    except json.JSONDecodeError:
        resultado["error"] = "Ollama no devolvió JSON válido"
        resultado["ficha"] = {"respuesta_cruda": data.get("response", "")}
    except Exception as e:
        resultado["error"] = str(e)

    return resultado
