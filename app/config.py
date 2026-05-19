import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = Path(os.getenv("DATA_PATH", BASE_DIR / "data"))


def project_path(value):
    path = Path(value)
    return path if path.is_absolute() else BASE_DIR / path


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-change-me")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

    DATABASE_PATH = project_path(os.getenv("DATABASE_PATH", DATA_PATH / "app.db"))
    STORAGE_PATH = project_path(os.getenv("STORAGE_PATH", BASE_DIR / "Download"))
    TELEGRAM_SESSION_PATH = project_path(os.getenv("TELEGRAM_SESSION_PATH", DATA_PATH / "telegram_session"))

    TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID", "")
    TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
    TELEGRAM_SESSION_NAME = os.getenv("TELEGRAM_SESSION_NAME", "telegram_session")

    DEFAULT_TELEGRAM_SEARCH_LIMIT = int(os.getenv("DEFAULT_TELEGRAM_SEARCH_LIMIT", "1000"))
    DEFAULT_TELEGRAM_CHANNELS = os.getenv("DEFAULT_TELEGRAM_CHANNELS", "schematicslaptop")
    MAX_DOWNLOAD_SIZE_MB = int(os.getenv("MAX_DOWNLOAD_SIZE_MB", "2048"))

    @classmethod
    def ensure_directories(cls):
        cls.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.STORAGE_PATH.mkdir(parents=True, exist_ok=True)
        cls.TELEGRAM_SESSION_PATH.mkdir(parents=True, exist_ok=True)
