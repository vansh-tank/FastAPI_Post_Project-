from pydantic_settings import BaseSettings


class Settings(BaseSettings):
  database_username: str = "root"
  database_password: str = "vanshtank"
  database_port: str = "3306"
  database_name: str = "FastAPI"
  database_hostname: str = "localhost"
  secret_key: str ="secret"
  algorithm: str = "HS256"
  access_token_expire_minutes: int = 30

  class Config:
    env_file = ".env"







settings = Settings()