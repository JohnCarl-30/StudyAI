from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Project
    PROJECT_NAME: str = "StudyAI API"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080

    # Pinecone (not ChromaDB!)
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str = "us-east-1"
    PINECONE_INDEX_NAME: str = "studyai"

    # OpenAI & Anthropic
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str

    # Storage
    UPLOAD_DIRECTORY: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_FILE_TYPES: list = ["application/pdf"]

    # App
    DEBUG: bool = False
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8080"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
