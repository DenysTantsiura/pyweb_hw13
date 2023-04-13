from fastapi import APIRouter, HTTPException, Depends, status, Security, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.database.db_connect import get_db
from src.repository import users as repository_users
from src.schemes import UserModel, UserResponse, TokenModel, RequestEmail
from src.services.auth import auth_service
from src.services.email import send_email


router = APIRouter(prefix='/auth', tags=['auth'])
security = HTTPBearer()


@router.post('/signup', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
                 body: UserModel,
                 background_tasks: BackgroundTasks, 
                 request: Request, 
                 db: Session = Depends(get_db)
                 ) -> dict:
    """обробляє операцію POST. Вона створює нового користувача, якщо користувача з такою електронною поштою не існує.
     Не може бути в системі два користувача з однаковим email. Якщо користувач з таким email вже існує в базі даних, 
     функція викликає виняток HTTPException з кодом стану 409 Conflict та подробицями detail='Account already exists'.
     """
    exist_user = await repository_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Account already exists')
    
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db)
    # Створюємо фонове завдання надсилання листа:
    background_tasks.add_task(send_email, new_user.email, new_user.username, request.base_url)
    # параметр request.base_url. Це атрибут об’єкта запиту Request, який є базовим URL запиту. 
    # Базовий URL включає схему (наприклад, http або https), ім’я хосту та порт, але не включає 
    # шлях або рядок запиту. У нашому випадку повний URL запиту буде http://127.0.0.1:8000/api/auth/signup, 
    # тоді request.base_url буде містити http://127.0.0.1:8000/. Цей атрибут ми використовуємо 
    # для генерації URL у шаблоні електронної пошти.

    return {'user': new_user, 'detail': 'User successfully created'}


@router.post('/login', response_model=TokenModel)
async def login(
                body: OAuth2PasswordRequestForm = Depends(),  # автоматом йде у Depends
                db: Session = Depends(get_db)
                ) -> dict:
    """обробляє операцію POST. Вона витягує користувача з бази даних з його email, якщо такого користувача немає, 
    то викликається виняток HTTPException з кодом стану 401 та подробицями detail='Invalid email'. 
    Після цього виконується перевірка пароля на збіг, якщо паролі не ідентичні, то викликається виняток HTTPException 
    з кодом стану 401 та подробицями detail='Invalid password'. Після всіх перевірок генерується пара 
    токенів access_token та refresh_token, для відправлення клієнту. Також оновлюємо токен оновлення у 
    базі даних для користувача."""
    user = await repository_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid email')
    
    if not user.confirmed:  # чи є email користувача верифікованим?
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Email not confirmed')
    
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid password')
    # Generate JWT
    access_token = await auth_service.create_access_token(data={'sub': user.email})
    refresh_token = await auth_service.create_refresh_token(data={'sub': user.email})
    await repository_users.update_token(user, refresh_token, db)

    return {'access_token': access_token, 'refresh_token': refresh_token, 'token_type': 'bearer'}


@router.get('/refresh_token', response_model=TokenModel)
async def refresh_token(
                        credentials: HTTPAuthorizationCredentials = Security(security), 
                        db: Session = Depends(get_db)
                        ) -> dict:
    """обробляє операцію GET. Вона декодує токен оновлення refresh_token та витягує відповідного користувача з БД. 
    Потім створює нові токени доступу та оновлення, і також оновлює refresh_token в базі даних для користувача. 
    Якщо токен оновлення недійсний, то викликається виняток HTTPException з кодом стану 401 та подробицями 
    detail='Invalid refresh token'."""
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repository_users.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid refresh token')

    access_token = await auth_service.create_access_token(data={'sub': email})
    refresh_token = await auth_service.create_refresh_token(data={'sub': email})
    await repository_users.update_token(user, refresh_token, db)

    return {'access_token': access_token, 'refresh_token': refresh_token, 'token_type': 'bearer'}


@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    """новий маршрут /confirm email/{token} для реалізації підтвердження електронної пошти. 
    Маршрут визначає операцію GET і приймає токен як параметр шляху.
    """
    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:  # Якщо користувача з отриманим email немає у DB, що вже підозріло, генеруємо 400 Bad request
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Verification error')
    
    # перевіряємо ситуацію, яким чином електронну пошту користувача вже підтверджено.   
    if user.confirmed:
        return {'message': 'Your email is already confirmed'}
    
    await repository_users.confirmed_email(email, db)

    return {'message': 'Email confirmed'}


@router.post('/request_email')
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                        db: Session = Depends(get_db)):
    """реалізує операцію POST для запиту повторної перевірки електронної пошти. Вона приймає тіло JSON з 
    адресою електронної пошти. Тому потрібно визначити модель RequestEmail у файлі src/shemas.py"""
    user = await repository_users.get_user_by_email(body.email, db)

    if user.confirmed:
        return {'message': 'Your email is already confirmed'}
    
    if user:
        background_tasks.add_task(send_email, user.email, user.username, request.base_url)
    
    #  листа надсилаємо, тільки якщо користувач існує в базі даних, 
    # а відповідь про успішне надсилання даємо завжди. Це не помилка, 
    # так ми страхуємося від випадку, якщо зловмисник вирішив перевірити, 
    # чи існує в системі незавершена реєстрація для електронного листа
    return {'message': 'Check your email for confirmation.'}