import os
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev_secret_change_me")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./storage/app.db")
IS_SQLITE_DATABASE = DATABASE_URL.startswith("sqlite")
RUN_DB_MIGRATIONS = os.getenv(
    "RUN_DB_MIGRATIONS",
    "false" if IS_SQLITE_DATABASE else "true"
).lower() == "true"
CHROMA_PATH = os.getenv("CHROMA_PATH", "./storage/chroma_db")
DATA_PATH = os.getenv("DATA_PATH", "./data/interview_qa.txt")
LOG_PATH = os.getenv("LOG_PATH", "./storage/app_events.jsonl")

IS_RAILWAY = bool(os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_ID"))
DEFAULT_FAKE_LLM = "true" if not DEEPSEEK_API_KEY else "false"
DEFAULT_FAKE_EMBEDDINGS = "true" if IS_RAILWAY else "false"

USE_FAKE_LLM = os.getenv("USE_FAKE_LLM", DEFAULT_FAKE_LLM).lower() == "true"
USE_FAKE_EMBEDDINGS = os.getenv("USE_FAKE_EMBEDDINGS", DEFAULT_FAKE_EMBEDDINGS).lower() == "true"
