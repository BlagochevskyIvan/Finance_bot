import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
BOT_ENABLED = os.getenv("BOT_ENABLED", "false").lower() in {"1", "true", "yes"}
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").rstrip("/")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/telegram")
WEBAPP_URL = os.getenv("WEBAPP_URL", "http://localhost:8081").rstrip("/")
TELEGRAM_SECRET = os.getenv("TELEGRAM_SECRET", "").strip()
DROP_PENDING = os.getenv("DROP_PENDING", "false").lower() in {"1", "true", "yes"}
BOT_CACHE_PATH = Path(os.getenv("BOT_CACHE_PATH", str(BASE_DIR / "data" / "bot_cache")))

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:password@localhost:5434/db",
)
DATABASE_URL_ALEMBIC = os.getenv(
    "DATABASE_URL_ALEMBIC",
    DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1),
)
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() in {"1", "true", "yes"}

if not WEBHOOK_PATH.startswith("/"):
    WEBHOOK_PATH = f"/{WEBHOOK_PATH}"

if BOT_ENABLED:
    missing = [
        name
        for name, value in {
            "TELEGRAM_TOKEN": TELEGRAM_TOKEN,
            "WEBHOOK_URL": WEBHOOK_URL,
            "TELEGRAM_SECRET": TELEGRAM_SECRET,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(
            f"BOT_ENABLED=true, but required settings are missing: {', '.join(missing)}"
        )
    if not WEBHOOK_URL.startswith("https://"):
        raise RuntimeError("WEBHOOK_URL must use HTTPS when the bot is enabled")
