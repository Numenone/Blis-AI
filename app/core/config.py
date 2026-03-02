from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # API Keys
    api_key: str = "blis_secret_token_123"  # Default dev key
    openrouter_api_key: str = ""
    tavily_api_key: str = ""
    
    # Redis
    redis_url: str = "redis://localhost:6379"

    # Supabase (Optional, for Vercel/Cloud deployment)
    supabase_url: str = ""
    supabase_service_key: str = ""

    # Server
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
