from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from backend.src.config import settings


DB_URL = settings.db_url.get_secret_value()

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)

Base = declarative_base()