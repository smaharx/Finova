import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in the environment.")

engine_kwargs = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        **engine_kwargs,
    )
else:
    connect_args = {}

    # Cloud PostgreSQL providers like Neon usually need SSL.
    if "sslmode=" not in DATABASE_URL:
        connect_args["sslmode"] = "require"

    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        **engine_kwargs,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
