from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"

    tushare_token: str | None = None
    iwencai_key: str | None = None
    finnhub_api_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
