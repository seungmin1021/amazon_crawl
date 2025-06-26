from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    access_key: str

    class Config:
        env_file = ".env"

settings = Settings()