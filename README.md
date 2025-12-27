# PliegoRAG

Aplicación web para analizar pliegos de condiciones de contratación estatal colombiana usando IA local (Ollama).

## Stack

- **Backend:** FastAPI (Python)
- **Base de datos:** MariaDB
- **IA:** Ollama con llama3.1
- **Contenedores:** Docker

## Requisitos

- Docker y Docker Compose
- Ollama corriendo con el modelo llama3.1

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/tu-usuario/pliegorag.git
cd pliegorag
```

2. Crear archivo de variables de entorno:
```bash
cp .env.example .env
```

3. Levantar contenedores:
```bash
docker-compose up --build
```

4. La API estará en: http://localhost:8000

## Endpoints

| Método | URL | Descripción |
|--------|-----|-------------|
| POST | /api/pliegos/upload | Subir PDF |
| GET | /api/pliegos | Listar pliegos |
| GET | /api/pliegos/{id} | Detalle de pliego |
| DELETE | /api/pliegos/{id} | Eliminar pliego |
| POST | /api/chat/preguntar | Hacer pregunta |
| GET | /api/chat/historial/{id} | Ver historial |
| POST | /api/chat/resumen | Generar resumen |
| GET | /health | Health check |

## Documentación API

Con la aplicación corriendo, visita: http://localhost:8000/docs

## Autor

Daniel Narváez - 2025