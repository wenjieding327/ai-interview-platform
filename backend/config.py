import os
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev_secret_change_me")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./storage/app.db")
CHROMA_PATH = os.getenv("CHROMA_PATH", "./storage/chroma_db")
DATA_PATH = os.getenv("DATA_PATH", "./data/interview_qa.txt")
LOG_PATH = os.getenv("LOG_PATH", "./storage/app_events.jsonl")

USE_FAKE_LLM = os.getenv("USE_FAKE_LLM", "false").lower() == "true"
USE_FAKE_EMBEDDINGS = os.getenv("USE_FAKE_EMBEDDINGS", "false").lower() == "true"
