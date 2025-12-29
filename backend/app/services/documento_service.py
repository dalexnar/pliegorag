from typing import List, Dict
import httpx
import json
from app.config import settings
from app.services.embedding_service import buscar_chunks_relevantes

# Lista base de documentos siempre requeridos en licitaciones colombianas
DOCUMENTOS_BASE = [
    {
        "nombre": "Certificado de Cámara de Comercio",
        "descripcion": "Certificado de existencia y representación legal (no mayor a 30 días)",
        "categoria": "habilitante_juridico",
        "siempre_requerido": True
    },
    {
        "nombre": "RUT (Registro Único Tributario)",
        "descripcion": "Registro Único Tributario actualizado",
        "categoria": "habilitante_juridico",
        "siempre_requerido": True
    },
    {
        "nombre": "Certificado de antecedentes fiscales",
        "descripcion": "Certificado de antecedentes fiscales expedido por Contraloría General de la República",
        "categoria": "habilitante_juridico",
        "siempre_requerido": True
    },
    {
        "nombre": "Certificado de antecedentes disciplinarios",
        "descripcion": "Certificado de antecedentes disciplinarios expedido por Procuraduría General de la Nación",
        "categoria": "habilitante_juridico",
        "siempre_requerido": True
    },
    {
        "nombre": "Certificado de antecedentes judiciales",
        "descripcion": "Certificado de antecedentes judiciales de la Policía Nacional",
        "categoria": "habilitante_juridico",
        "siempre_requerido": True
    },
    {
        "nombre": "Certificado de pago de aportes a seguridad social",
        "descripcion": "Certificación de pago de aportes a seguridad social (salud, pensión, ARL)",
        "categoria": "habilitante_juridico",
        "siempre_requerido": True
    },
    {
        "nombre": "Garantía de seriedad de la oferta",
        "descripcion": "Póliza o garantía que respalde la seriedad de la oferta",
        "categoria": "garantias",
        "siempre_requerido": True
    },
    {
        "nombre": "Carta de presentación de la propuesta",
        "descripcion": "Carta firmada por el representante legal presentando la oferta",
        "categoria": "propuesta",
        "siempre_requerido": True
    }
]


def detectar_documentos_adicionales(texto_pliego: str, pliego_id: int) -> Dict:
    """
    Usa IA para detectar documentos adicionales específicos del pliego.

    Args:
        texto_pliego: Texto completo del pliego
        pliego_id: ID del pliego para buscar chunks relevantes

    Returns:
        Dict con documentos detectados y error si hay
    """
    resultado = {
        "documentos": [],
        "error": None
    }

    # Buscar chunks relevantes sobre requisitos y documentos
    try:
        chunks_requisitos = buscar_chunks_relevantes("requisitos documentos habilitantes", pliego_id, n_resultados=5)
        chunks_experiencia = buscar_chunks_relevantes("experiencia certificaciones", pliego_id, n_resultados=3)
        chunks_tecnicos = buscar_chunks_relevantes("especificaciones técnicas documentos", pliego_id, n_resultados=3)

        # Combinar chunks
        chunks_combinados = chunks_requisitos + chunks_experiencia + chunks_tecnicos

        # Crear contexto para el LLM
        contexto = "\n\n".join([f"[Página {c['page']}, Sección: {c['section']}]\n{c['texto']}" for c in chunks_combinados[:8]])

        prompt = f"""Eres un experto en contratación estatal colombiana.
Analiza el siguiente extracto del pliego y extrae ÚNICAMENTE los documentos ESPECÍFICOS requeridos que NO estén en esta lista base:
- Certificado de Cámara de Comercio
- RUT
- Antecedentes fiscales, disciplinarios y judiciales
- Certificado de aportes a seguridad social
- Garantía de seriedad de la oferta
- Carta de presentación

EXTRACTO DEL PLIEGO:
{contexto}

Identifica documentos ADICIONALES como:
- Certificaciones de experiencia específicas
- Licencias o permisos especiales
- Certificados técnicos o de calidad
- Documentos financieros específicos
- Certificaciones de personal
- Autorizaciones especiales

Responde ÚNICAMENTE con un JSON válido en este formato:
{{
  "documentos": [
    {{
      "nombre": "nombre del documento",
      "descripcion": "descripción breve",
      "categoria": "experiencia|tecnico|financiero|legal|otros",
      "mencionado_en": "texto exacto donde se menciona (máximo 200 caracteres)"
    }}
  ]
}}

Si no hay documentos adicionales específicos, retorna: {{"documentos": []}}"""

        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{settings.OLLAMA_HOST}/api/generate",
                json={
                    "model": "llama3.1:latest",
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            data = response.json()

        respuesta_texto = data.get("response", "{}")

        # Limpiar respuesta (a veces viene con texto adicional)
        # Buscar el primer { y último }
        inicio = respuesta_texto.find("{")
        fin = respuesta_texto.rfind("}") + 1

        if inicio != -1 and fin > inicio:
            json_limpio = respuesta_texto[inicio:fin]
            documentos_detectados = json.loads(json_limpio)
            resultado["documentos"] = documentos_detectados.get("documentos", [])
        else:
            resultado["error"] = "No se pudo extraer JSON de la respuesta"

    except json.JSONDecodeError as e:
        resultado["error"] = f"Error al parsear JSON: {str(e)}"
    except Exception as e:
        resultado["error"] = f"Error al detectar documentos: {str(e)}"

    return resultado


def encontrar_referencias_documento(nombre_documento: str, descripcion: str, pliego_id: int) -> List[Dict]:
    """
    Busca en qué páginas/secciones se menciona un documento específico.

    Args:
        nombre_documento: Nombre del documento a buscar
        descripcion: Descripción del documento
        pliego_id: ID del pliego

    Returns:
        Lista de referencias con página y sección
    """
    referencias = []

    try:
        # Buscar chunks que mencionen este documento
        query = f"{nombre_documento} {descripcion}"
        chunks = buscar_chunks_relevantes(query, pliego_id, n_resultados=3)

        # Extraer referencias únicas
        for chunk in chunks:
            ref = {
                "page": chunk.get("page", 1),
                "section": chunk.get("section", "sin_seccion"),
                "extracto": chunk.get("texto", "")[:200] + "..." if len(chunk.get("texto", "")) > 200 else chunk.get("texto", "")
            }

            # Evitar duplicados
            if not any(r["page"] == ref["page"] and r["section"] == ref["section"] for r in referencias):
                referencias.append(ref)

    except Exception as e:
        print(f"Error al buscar referencias para {nombre_documento}: {str(e)}")

    return referencias


def generar_checklist_completo(pliego_id: int, texto_pliego: str) -> Dict:
    """
    Genera checklist completo de documentos: base + detectados por IA.

    Args:
        pliego_id: ID del pliego
        texto_pliego: Texto completo del pliego

    Returns:
        Dict con checklist completo y metadatos
    """
    resultado = {
        "documentos_base": [],
        "documentos_especificos": [],
        "total_documentos": 0,
        "error": None
    }

    try:
        # 1. Procesar documentos base y encontrar referencias
        for doc_base in DOCUMENTOS_BASE:
            doc_con_refs = doc_base.copy()
            referencias = encontrar_referencias_documento(
                doc_base["nombre"],
                doc_base["descripcion"],
                pliego_id
            )
            doc_con_refs["referencias"] = referencias
            resultado["documentos_base"].append(doc_con_refs)

        # 2. Detectar documentos adicionales con IA
        deteccion = detectar_documentos_adicionales(texto_pliego, pliego_id)

        if deteccion["error"]:
            resultado["error"] = f"Advertencia al detectar documentos específicos: {deteccion['error']}"

        # 3. Procesar documentos específicos detectados
        for doc_especifico in deteccion.get("documentos", []):
            referencias = encontrar_referencias_documento(
                doc_especifico.get("nombre", ""),
                doc_especifico.get("descripcion", ""),
                pliego_id
            )
            doc_especifico["referencias"] = referencias
            doc_especifico["siempre_requerido"] = False
            resultado["documentos_especificos"].append(doc_especifico)

        # 4. Calcular total
        resultado["total_documentos"] = len(resultado["documentos_base"]) + len(resultado["documentos_especificos"])

    except Exception as e:
        resultado["error"] = f"Error al generar checklist: {str(e)}"

    return resultado
