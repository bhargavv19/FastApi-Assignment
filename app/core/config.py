from typing import List, Union, Any, Dict, Optional
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator, PostgresDsn

class Settings(BaseSettings):
    PROJECT_NAME: str = "Chat API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = ["*"]  # Allow all origins in development

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # PostgreSQL Configuration
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "chat_db"
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return f"postgresql://{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_SERVER')}/{values.get('POSTGRES_DB')}"

    # MongoDB Configuration
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "chat_db"
    MONGODB_UUID_REPRESENTATION: str = "standard"

    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # JWT Configuration
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings() 