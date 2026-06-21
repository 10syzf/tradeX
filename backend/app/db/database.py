from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import get_settings

settings = get_settings()
database_url = settings.database_url

if database_url.startswith('sqlite:///'):
    db_path = database_url.replace('sqlite:///', '', 1)
    db_file = Path(db_path)
    if not db_file.is_absolute():
        db_file = Path(__file__).resolve().parents[3] / db_file
    db_file.parent.mkdir(parents=True, exist_ok=True)
    database_url = f'sqlite:///{db_file}'

engine = create_engine(
    database_url,
    connect_args={'check_same_thread': False} if database_url.startswith('sqlite') else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
