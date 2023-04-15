"""
визначимо клас служби аутентифікації Auth. 
Вона має кілька методів для підтримки операцій аутентифікації та авторизації.
"""
from datetime import datetime, timedelta
import os
import pickle
from typing import Optional

from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
import redis
# from redis_lru import RedisLRU
from sqlalchemy.orm import Session

from src.database.db_connect import get_db
from src.repository import users as repository_users
from src.authentication import get_password


class Auth:
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
    SECRET_KEY = 'secret_key'
    ALGORITHM = 'HS256'
    """забезпечує авторизацію по bearer токену. Він потрібний для валідації JWT токена, 
    який буде використовуватися як аутентифікаційні дані користувача.
    вказуємо йому, де в нашому застосунку буде маршрут для аутентифікації tokenUrl='/api/auth/login'. І
    він, відповідно до стандарту, очікує на пару username і password, але, 
    замість значення username, будемо підставляти в полі email користувача."""
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login')  # 
    # https://dev.to/ramko9999/host-and-use-redis-for-free-51if
    # Redis connect (to connect.py? but @cache, ... but external get_password()...):
    client = redis.Redis(
            host='redis-12148.c135.eu-central-1-1.ec2.cloud.redislabs.com',
            port=12148,
            password=os.environ.get('REDIS_KEY') or get_password('key_redis.txt'))
            
    # cache = RedisLRU(client)

    def verify_password(self, plain_password, hashed_password) -> bool:
        """перевіряє, чи відповідає простий текстовий пароль хешованому паролю."""
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        """хешує пароль за допомогою алгоритму bcrypt. (look at line 31)
        повертає зашифрований пароль, згенерований за допомогою методу hash з класу CryptContext."""
        return self.pwd_context.hash(password)

    # define a function to generate a new access token
    async def create_access_token(self, data: dict, expires_delta: Optional[float] = None):
        """створює веб-токен JWT з областю дії scope, що дорівнює значенню access_token, 
        який буде використовуватись для авторизації користувача для доступу до захищених ресурсів.
        приймає два параметри:
        data - словник, що містить корисні дані для кодування у форматі JWT;
        expires_delta - необов'язковий параметр, що визначає час життя токена в секундах. 
            Якщо параметр не вказано, час життя за замовчуванням складає 15 хвилин."""
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
        """створює JWT з областю дії refresh_token, який можна використовувати для оновлення 
        токена доступу access_token після закінчення терміну його дії.
        аналогічний методу create_access_token, але за замовчуванням має час життя 7 днів і 
        область дії `scope'': 'refresh_token'."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)

        else:
            expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({'iat': datetime.utcnow(), 'exp': expire, 'scope': 'refresh_token'})
        encoded_refresh_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

        return encoded_refresh_token

    async def decode_refresh_token(self, refresh_token: str):
        """метод декодує токен оновлення refresh_token для отримання електронної пошти користувача.
        декодує токен оновлення refresh_token та повертає з корисного навантаження email користувача. 
        Якщо корисне навантаження токена не має області дії, що дорівнює 'refresh_token', воно 
        викликає виняток HTTPException з кодом стану 401 та подробицями detail=..."""
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
        """авторизує користувача, розшифровуючи токен доступу access_token та, перевіряючи існування користувача у БД.
        використовується для авторизації користувача на основі його токена доступу: access_token. 
        При цьому ми використовуємо клас OAuth2PasswordBearer для витягування токена із запиту, а потім 
        декодуємо токен payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM]) 
        з використанням атрибутів SECRET_KETH класу Auth."""
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

        # redis cach: ... or @cache if LRU... https://developer.redis.com/develop/python/fastapi/
        # user = await repository_users.get_user_by_email(email, db)
        user = self.client.get(f'user:{email}')
        if user is None:
            user = await repository_users.get_user_by_email(email, db)
            if user is None:
                raise credentials_exception
            
            self.client.set(f"user:{email}", pickle.dumps(user))
            self.client.expire(f"user:{email}", 900)

        else:
            user = pickle.loads(user)

        # if user is None:
        #     raise credentials_exception
        
        return user
    
    def create_email_token(self, data: dict):
        """Всередині сервісу Auth реалізуємо метод create_email_token.
        Поверни закодований токен, що дійсний 7 днів. Саме стільки ми чекатимемо від 
        користувача верифікації. А, оскільки під час створення в полі sub ми помістили email, 
        він повністю персоналізований для користувача.

        Далі створюємо об’єкт MessageSchema із зазначеними темою, одержувачами та тілом шаблону, 
        а потім передаємо його об’єкту FastMail. 
        Наприкінці викликаємо метод send_message, що передає повідомлення та ім’я шаблону email_template.html. 
        Сам шаблон знаходиться в папці templates."""
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
        """створює веб-токен JWT з областю дії scope, що дорівнює значенню password_reset_token, 
        який буде використовуватись для скидання паролю користувача.
        приймає два параметри:
        data - словник, що містить корисні дані для кодування у форматі JWT;
        expires_delta - необов'язковий параметр, що визначає час життя токена в секундах. 
            Якщо параметр не вказано, час життя за замовчуванням складає 45 хвилин."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)

        else:
            expire = datetime.utcnow() + timedelta(minutes=45)
        to_encode.update({'iat': datetime.utcnow(), 'exp': expire, 'scope': 'password_reset_token'})
        encoded_password_reset_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

        return encoded_password_reset_token
        
    async def reset_password(self, token: str):  # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        """ генерує посилання для скидання паролю, яке буде використовуватися лише один раз. 
        Після цього надсилає це посилання на адресу електронної пошти користувача."""
        
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload['sub']

            return email
        
        except JWTError as e:
            print(e)
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail='Invalid token for password reset')


auth_service = Auth()  # будемо використовувати у всьому коді для виконання операцій аутентифікації та авторизації
