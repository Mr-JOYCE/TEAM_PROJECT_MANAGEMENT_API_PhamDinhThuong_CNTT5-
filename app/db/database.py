from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy_utils import database_exists, create_database

from ..core.config import settings

if not database_exists(settings.DATABASE_URL):
    create_database(settings.DATABASE_URL)

engine = create_engine(settings.DATABASE_URL, echo=True)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False        
)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()

    try: 
        yield db
    finally:
        db.close()