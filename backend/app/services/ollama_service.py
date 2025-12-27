import httpx
import time
from app.config import settings


def preguntar_ollama(texto_pliego: str, pregunta: str) -> dict:
    """
    Envía una pregunta a Ollama con el contexto del pliego.
    Retorna dict con respuesta, tokens, tiempo, y error si hay.
    """
    resultado = {
        "respuesta": "",
        "tokens_prompt": 0,
        "tokens_respuesta": 0,
        "tiempo_ms": 0,
        "error": None
    }

    prompt = f"""Eres un experto en contratación estatal colombiana. 
Analiza el siguiente pliego de condiciones y responde la pregunta del usuario.

PLIEGO DE CONDICIONES:
{texto_pliego}

PREGUNTA DEL USUARIO:
{pregunta}

Responde de forma clara y concisa, citando las partes relevantes del pliego cuando sea posible."""

    try:
        inicio = time.time()

        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{settings.OLLAMA_HOST}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False
                }
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
    """
    Genera una ficha resumen estructurada del pliego.
    """
    resultado = {
        "ficha": {},
        "error": None
    }

    prompt = f"""Eres un experto en contratación estatal colombiana.
Analiza el siguiente pliego de condiciones y extrae la información clave.

PLIEGO DE CONDICIONES:
{texto_pliego}

Responde ÚNICAMENTE con un JSON válido (sin texto adicional) con esta estructura:
{{
    "numero_proceso": "número o código del proceso",
    "entidad": "nombre de la entidad contratante",
    "objeto": "objeto del contrato (resumido)",
    "presupuesto": "presupuesto oficial",
    "fecha_cierre": "fecha límite para presentar ofertas",
    "experiencia_requerida": "requisitos de experiencia",
    "garantias": "garantías solicitadas",
    "criterios_evaluacion": "criterios y ponderación",
    "observaciones": "puntos importantes a tener en cuenta"
}}"""

    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{settings.OLLAMA_HOST}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False
                }
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