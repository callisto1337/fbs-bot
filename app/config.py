from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    max_bot_token: str
    database_url: str
    admin_secret_key: str
    admin_username: str
    admin_password: str


settings = Settings()
