from pydantic.v1 import BaseSettings


class Config(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@postgresql:5432/application-db"
    TEST_DATABASE_URL: str = "sqlite+aiosqlite://"


config: Config = Config()

