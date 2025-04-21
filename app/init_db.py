from app.database import Base, engine
from app.models.JobPost import JobPost  # 👈 ensure the model is imported
from app.log_config import logger


def init_db():
    print("📦 Creating tables if they do not exist...")
    logger.info("Creating tables if they do not exist...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized!")
    logger.info("Database initialized!")
