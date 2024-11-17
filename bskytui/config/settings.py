from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bsky_handle: str
    bsky_password: str
    timezone: str = "America/Chicago"
