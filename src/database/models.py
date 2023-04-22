from sqlalchemy import Column, Date, func, Integer, String, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import DateTime

from src.database.db_connect import Base


class Contact(Base):
    """Base Contact class."""
    __tablename__: str = 'contacts'
    id = Column(Integer, primary_key=True)
    name = Column(String(30), index=True)
    last_name = Column(String(40), index=True)
    email = Column(String(30), unique=True, index=True)
    phone = Column(Integer, unique=True, index=True)
    birthday = Column(Date, index=True, nullable=True)
    description = Column(String(3000))
    user_id = Column('user_id', ForeignKey('users.id', ondelete='CASCADE'), default=None)
    user = relationship('User', backref='users')
    # creates a connection between classes and indicates that the connection is an m2m connection
    # backref creates a back reference to the User class, allowing the associated Contact objects
    # to be accessed from the User object


class User(Base):
    """Base User class."""
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    email = Column(String(30), nullable=False, unique=True)
    password = Column(String(255), nullable=False)  # not 10, because store hash, not password
    created_at = Column('crated_at', DateTime, default=func.now())
    avatar = Column(String(255), nullable=True)
    refresh_token = Column(String(255), nullable=True)
    confirmed = Column(Boolean, default=False)  # whether the user's email was confirmed
