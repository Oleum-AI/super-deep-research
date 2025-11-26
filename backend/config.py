from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM Provider API Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    xai_api_key: str = ""
    xai_base_url: str = "https://api.x.ai/v1"
    brave_search_api_key: str = ""

    # Server Configuration
    backend_port: int = 8001
    frontend_port: int = 5173

    # Database
    database_url: str = "sqlite+aiosqlite:///./research.db"

    # CORS Origins
    frontend_url: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Allow extra fields in .env file


settings = Settings()
