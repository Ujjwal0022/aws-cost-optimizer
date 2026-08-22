from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_DEFAULT_REGION: str = "us-east-1"
    AWS_ACCOUNT_ID: str = ""
    CORS_ORIGINS: str = "*"

    class Config:
        env_file = ".env"

settings = Settings()
