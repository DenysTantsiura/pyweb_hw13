import logging
from typing import Optional

from sqlalchemy import (
    create_engine, 
    Engine,
    )
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.conf.config import settings


logging.basicConfig(level=logging.DEBUG, format='%(threadName)s %(message)s')

SQLALCHEMY_DATABASE_URL = settings.sqlalchemy_database_url


def create_connection(*args, **kwargs) -> tuple[Optional[Engine], Optional[sessionmaker]]:
    """Create a database connection (session) to a PostgreSQL database (engine)."""
    try:
        engine_ = create_engine(SQLALCHEMY_DATABASE_URL, echo=True, pool_size=10)
        db_session = sessionmaker(autocommit=False, autoflush=False, bind=engine_)
    
    except Exception as error:
        logging.error(f'Wrong connect. error:\n{error}')
        return None, None

    return engine_, db_session


engine, SessionLocal = create_connection()


Base = declarative_base()


# Dependency
def get_db():
    """Returns a session using a factory: SessionLocal."""  
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
