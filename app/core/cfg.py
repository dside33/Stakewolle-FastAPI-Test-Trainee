from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: str
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    SECRET:str
    ALGORITHM:str
    ACCESS_TOKEN_EXPIRE_MINUTES:int
    ISSUER:str

    class Config:
        env_file = ".env"



settings = Settings()
