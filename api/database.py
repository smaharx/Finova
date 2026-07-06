import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# If no DATABASE_URL provided, default to a local sqlite file (for local dev)
# This keeps the README instruction ("expenses.db auto-generate") working.
if not DATABASE_URL:
    local_sqlite_path = os.path.join(os.getcwd(), "expenses.db")
    DATABASE_URL = f"sqlite:///{local_sqlite_path}"

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

    # Cloud PostgreSQL providers often need SSL. If DATABASE_URL already contains sslmode, respect it.
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
