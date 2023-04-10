from sqlalchemy import Column, Date, func, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import DateTime

from src.database.db_connect import Base


class Contact(Base):
    __tablename__: str = "contacts"
    id = Column(Integer, primary_key=True)
    name = Column(String(30), index=True)
    last_name = Column(String(40), index=True)
    email = Column(String(30), unique=True, index=True)
    phone = Column(Integer, unique=True, index=True)
    birthday = Column(Date, index=True, nullable=True)
    description = Column(String(3000))
    user_id = Column('user_id', ForeignKey('users.id', ondelete='CASCADE'), default=None)
    user = relationship('User', backref="users")  # створює зв'язок між класами і вказує, що зв'язок є зв'язком m2m
    # backref створює зворотне посилання на клас User,
    # дозволяючи отримати доступ до зв'язаних об'єктів Contact з об'єкта User


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    email = Column(String(30), nullable=False, unique=True)
    password = Column(String(255), nullable=False)  # not 10, because store hash, not password
    created_at = Column('crated_at', DateTime, default=func.now())
    avatar = Column(String(255), nullable=True)
    refresh_token = Column(String(255), nullable=True)
