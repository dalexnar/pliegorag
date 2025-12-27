from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import pliegos_router, chat_router

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PliegoRAG API",
    description="API para analizar pliegos de condiciones con IA",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(pliegos_router)
app.include_router(chat_router)


@app.get("/")
def root():
    return {"mensaje": "PliegoRAG API", "version": "1.0.0"}


@app.get("/health")
def health_check():
    return {"status": "ok"}