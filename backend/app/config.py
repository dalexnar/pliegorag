from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Base de datos
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "pliegorag"
    DB_USER: str = "root"
    DB_PASSWORD: str = ""

    # Ollama
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:latest"

    class Config:
        env_file = ".env"


settings = Settings()