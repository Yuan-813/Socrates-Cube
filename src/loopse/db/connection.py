"""SQLAlchemy database connection management."""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "edu_agent.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=os.getenv("SQL_ECHO", "0") == "1",
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    """Create all declared tables."""
    from src.loopse.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
