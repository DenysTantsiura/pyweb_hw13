from datetime import datetime, timedelta
import pickle
from typing import Optional

from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
import redis
from sqlalchemy.orm import Session

from src.database.db_connect import get_db
from src.repository import users as repository_users
from src.conf.config import settings


class Auth:
    """The main class for authentication functions."""
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
    SECRET_KEY = settings.secret_key
    ALGORITHM = settings.algorithm

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login')
    # https://dev.to/ramko9999/host-and-use-redis-for-free-51if
    client = redis.Redis(
                         host=settings.redis_host,
                         port=settings.redis_port,
                         password=settings.redis_password
                         )

    def verify_password(self, plain_password, hashed_password) -> bool:
        """
        The verify_password function takes a plain-text password and hashed password as arguments.
        It then uses the verify method of the pwd_context object to check if they match.
        The result is returned as a boolean value.

        :param self: Represent the instance of the class
        :param plain_password: Pass in the password that is being checked
        :param hashed_password: Compare the hashed password in the database with a plain text password
        :return: A boolean value
        :doc-author: Trelent
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        """
        The get_password_hash function takes a password as input and returns the hash of that password.
        The hash is generated using the pwd_context object, which is an instance of Flask-Bcrypt's Bcrypt class.

        :param self: Represent the instance of the class
        :param password: str: Pass the password to be hashed
        :return: A password hash
        :doc-author: Trelent
        """
        return self.pwd_context.hash(password)

    # define a function to generate a new access token
    async def create_access_token(self, data: dict, expires_delta: Optional[float] = None):
        """
        The create_access_token function creates a new access token.
            Args:
                data (dict): A dictionary containing the claims to be encoded in the JWT.
                expires_delta (Optional[float]): An optional timedelta of seconds for the expiration time of this token.

        :param self: Represent the instance of the class
        :param data: dict: Pass the data that will be encoded into the token
        :param expires_delta: Optional[float]: Set the expiration time of the access token
        :return: An encoded access token
        :doc-author: Trelent
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)

        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({'iat': datetime.utcnow(), 'exp': expire, 'scope': 'access_token'})
        encoded_access_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

        return encoded_access_token

    # define a function to generate a new refresh token
    async def create_refresh_token(self, data: dict, expires_delta: Optional[float] = None):
        """
        The create_refresh_token function creates a refresh token for the user.
            Args:
                data (dict): A dictionary containing the user's id and username.
                expires_delta (Optional[float]): The time in seconds until the refresh token expires. Defaults to None,
                which is 7 days from creation date.

        :param self: Make the function a method of the class
        :param data: dict: Pass the data to be encoded
        :param expires_delta: Optional[float]: Set the expiration time of the refresh token
        :return: A refresh token
        :doc-author: Trelent
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)

        else:
            expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({'iat': datetime.utcnow(), 'exp': expire, 'scope': 'refresh_token'})
        encoded_refresh_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

        return encoded_refresh_token

    async def decode_refresh_token(self, refresh_token: str):
        """
        The decode_refresh_token function is used to decode the refresh token.

        :param self: Represent the instance of the class
        :param refresh_token: str: Pass in the refresh token that is being decoded
        :return: The email of the user who is trying to refresh their access token
        :doc-author: Trelent
        """
        try:
            payload = jwt.decode(refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'refresh_token':
                email = payload['sub']

                return email
            
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid scope for token')
        
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate credentials')

    # @cache
    async def get_current_user(self, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        """
        The get_current_user function is a dependency that will be used in the
            protected endpoints. It uses the OAuth2 Dependency to retrieve a user's JWT from
            the Authorization header. Then it decodes and verifies this token with our SECRET_KEY,
            which was generated when we ran uvicorn for the first time. If everything checks out,
            then we return an object of type UserInDB (which is defined in schemas/users).

        :param self: Represent the instance of the class
        :param token: str: Get the token from the authorization header
        :param db: Session: Get the current database session
        :return: A user object
        :doc-author: Trelent
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate credentials',
            headers={'WWW-Authenticate': 'Bearer'},
            )

        try:
            # Decode JWT
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'access_token':
                email = payload['sub']
                if email is None:
                    raise credentials_exception
                
            else:
                raise credentials_exception
            
        except JWTError as e:
            print(e)
            raise credentials_exception

        # https://developer.redis.com/develop/python/fastapi/
        user = self.client.get(f'user:{email}')
        if user is None:
            user = await repository_users.get_user_by_email(email, db)
            if user is None:
                raise credentials_exception
            
            self.client.set(f"user:{email}", pickle.dumps(user))
            self.client.expire(f"user:{email}", 900)

        else:
            user = pickle.loads(user)
        
        return user
    
    def create_email_token(self, data: dict):
        """
        The create_email_token function takes in a dictionary of data and returns a token.
        The token is created by encoding the data with the SECRET_KEY and ALGORITHM.
        The encoded data includes an 'iat' (issued at) timestamp, as well as an expiration date 7 days from now.

        :param self: Make the function a method of the class
        :param data: dict: Pass in the user's email address and username
        :return: A token that is encoded with the user's email address, a timestamp and an expiration date
        :doc-author: Trelent
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({'iat': datetime.utcnow(), 'exp': expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

        return token

    async def get_email_from_token(self, token: str):
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload['sub']

            return email
        
        except JWTError as e:
            print(e)
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail='Invalid token for email verification')

    # define a function to generate a new access token
    async def create_password_reset_token(self, data: dict, expires_delta: Optional[float] = None):
        """
        The create_password_reset_token function creates a password reset token for the user.
            The function takes in two arguments: data and expires_delta. Data is a dictionary containing the user's
            email address, while expires_delta is an optional argument that specifies how long the token will be valid
            for (in seconds).
            If no value is passed to expires_delta, then it defaults to 45 minutes.

        :param self: Access the class attributes and methods
        :param data: dict: Pass in the user's email address
        :param expires_delta: Optional[float]: Set the expiration time for the token
        :return: A jwt token
        :doc-author: Trelent
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)

        else:
            expire = datetime.utcnow() + timedelta(minutes=45)
        to_encode.update({'iat': datetime.utcnow(), 'exp': expire, 'scope': 'password_reset_token'})
        encoded_password_reset_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

        return encoded_password_reset_token
        
    async def reset_password(self, token: str):
        """
        The reset_password function takes a token as an argument and returns the email address of the user who requested
        the password reset. The function first decodes the token using PyJWT, then extracts and returns
        the email address from
        the payload.

        :param self: Represent the instance of the class
        :param token: str: Pass in the token that was sent to the user's email
        :return: The email of the user who requested a password reset
        :doc-author: Trelent
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload['sub']

            return email
        
        except JWTError as e:
            print(e)
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail='Invalid token for password reset')


auth_service = Auth()
