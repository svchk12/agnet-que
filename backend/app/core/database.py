import os
if os.environ.get("TESTING") == "1":
    from app.core.test_config import test_settings
    DATABASE_URL = test_settings.DATABASE_URL
else:
    from app.core.config import settings
    DATABASE_URL = settings.DATABASE_URL

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 