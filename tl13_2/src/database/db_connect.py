# підключення до бази даних (sqlite/PostgreSQL)
import configparser  # for work with *.ini (config.ini)
import logging
import pathlib
from typing import Optional

from sqlalchemy import (
    create_engine, 
    Engine,
    )
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.authentication import get_password


CONFIG_FILE = 'config.ini'

logging.basicConfig(level=logging.DEBUG, format='%(threadName)s %(message)s')

file_config = pathlib.Path(__file__).parent.parent.joinpath(CONFIG_FILE)  # try?
config = configparser.ConfigParser()
config.read(file_config)

user = config.get('DB_DEV', 'user')
password = get_password()
database = config.get('DB_DEV', 'db_name')
host = config.get('DB_DEV', 'host')
port = config.get('DB_DEV', 'port')

SQLALCHEMY_DATABASE_URL = f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}'
if port == '0':
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(':0/', '/')


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
