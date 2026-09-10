import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.engine import make_url

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev_secret_change_me")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

BACKEND_ROOT = Path(__file__).resolve().parent
STORAGE_PATH = Path(os.getenv("RAILWAY_VOLUME_MOUNT_PATH", str(BACKEND_ROOT / "storage")))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(STORAGE_PATH / 'app.db').as_posix()}")
if DATABASE_URL.startswith(("postgres://", "postgresql://")):
    DATABASE_URL = make_url(DATABASE_URL.replace("postgres://", "postgresql://", 1)).set(
        drivername="postgresql+psycopg"
    ).render_as_string(hide_password=False)
IS_SQLITE_DATABASE = DATABASE_URL.startswith("sqlite")
RUN_DB_MIGRATIONS = os.getenv(
    "RUN_DB_MIGRATIONS",
    "false" if IS_SQLITE_DATABASE else "true"
).lower() == "true"
CHROMA_PATH = os.getenv("CHROMA_PATH", str(STORAGE_PATH / "chroma_db"))
DATA_PATH = os.getenv("DATA_PATH", str(BACKEND_ROOT / "data" / "interview_qa.txt"))
LOG_PATH = os.getenv("LOG_PATH", str(STORAGE_PATH / "app_events.jsonl"))

IS_RAILWAY = bool(os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_ID"))
DEFAULT_FAKE_LLM = "false"
DEFAULT_FAKE_EMBEDDINGS = "true" if IS_RAILWAY else "false"

USE_FAKE_LLM = os.getenv("USE_FAKE_LLM", DEFAULT_FAKE_LLM).lower() == "true"
USE_FAKE_EMBEDDINGS = os.getenv("USE_FAKE_EMBEDDINGS", DEFAULT_FAKE_EMBEDDINGS).lower() == "true"
RETRIEVAL_MODE = os.getenv("RETRIEVAL_MODE", "lexical")
if RETRIEVAL_MODE not in {"lexical", "vector"}:
    raise ValueError("RETRIEVAL_MODE must be lexical or vector")
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
MAX_INTERVIEW_TURNS = int(os.getenv("MAX_INTERVIEW_TURNS", "6"))
ADMIN_EMAILS = {email.strip().lower() for email in os.getenv("ADMIN_EMAILS", "").split(",") if email.strip()}
