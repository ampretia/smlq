from pydantic_settings import BaseSettings
from typing import Set


class Settings(BaseSettings):
    database_path: str = "/opt/smlq/data"
    database_file_name: str = "smlq_v2.db"

    default_queues: Set[str] = set(["input","output"])

    class Config:
        env_file = "/data/env/.env", ".env"


settings = Settings()
