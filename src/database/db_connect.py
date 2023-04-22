"""Connection to DataBase."""
import logging
from typing import Optional

from sqlalchemy import create_engine, Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.conf.config import settings


logging.basicConfig(level=logging.DEBUG, format='%(threadName)s %(message)s')

SQLALCHEMY_DATABASE_URL = settings.sqlalchemy_database_url


def create_connection(*args, **kwargs) -> tuple[Optional[Engine], Optional[sessionmaker]]:
    """
    The create_connection function creates a connection to the database.
        Args:
            `*args` (tuple): A tuple of arguments.
            `**kwargs` (dict): A dictionary of keyword arguments.

    :param `*args`: Send a non-keyworded variable length argument list to the function
    :param `**kwargs`: Pass a variable number of keyword arguments to a function
    :return: A tuple of two values: an engine and a session
    :doc-author: Trelent
    """
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
    """
    The get_db function is a context manager that returns the database session.
    It also ensures that the connection to the database is closed after each request.

    :return: A database session
    :doc-author: Trelent
    """
    db = SessionLocal()
    try:
        yield db

    finally:
        db.close()
