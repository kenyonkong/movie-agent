from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Movie Agent API"
    app_version: str = "0.1.0"
    environment: str = "development"


settings = Settings()