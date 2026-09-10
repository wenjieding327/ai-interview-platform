from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import DATABASE_URL
from pathlib import Path
from sqlalchemy.engine import make_url

database_url = make_url(DATABASE_URL)
if database_url.get_backend_name() == "sqlite" and database_url.database not in (None, "", ":memory:"):
    Path(database_url.database).expanduser().parent.mkdir(parents=True, exist_ok=True)

connect_args = {"check_same_thread": False, "timeout": 30} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=not DATABASE_URL.startswith("sqlite")
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()
