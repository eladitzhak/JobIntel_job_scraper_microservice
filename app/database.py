from sqlalchemy.orm import declarative_base

# Base = declarative_base()
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

Base = declarative_base()
# engine = create_engine(settings.POSTGRES_URL)
engine = create_engine(str(settings.POSTGRES_URL), echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
