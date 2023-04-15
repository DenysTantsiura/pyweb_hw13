from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from src.conf.config import settings
from src.services.auth import auth_service


conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=EmailStr(settings.mail_from),
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_FROM_NAME=settings.mail_from_name,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent / 'templates',
    )


async def send_email(email: EmailStr, username: str, host: str):
    """Приймає три аргументи – адресу електронної пошти одержувача, ім’я користувача 
    і хост, де працює наш застосунок. Насамперед створюємо токен JWT для верифікації 
    електронної пошти за допомогою методу auth_service.create_email_token. Потім 
    цей токен передається в шаблон електронної пошти як змінна за допомогою 
    параметра template_body.
    (створюємо об’єкт MessageSchema із зазначеними темою, одержувачами та тілом шаблону, 
    а потім передаємо його об’єкту FastMail. Наприкінці викликаємо метод send_message, 
    що передає повідомлення та ім’я шаблону email_template.html. 
    Сам шаблон знаходиться в папці templates)
    """
    subject = 'Confirm your email '
    try:
        token_verification = auth_service.create_email_token({'sub': email})
        message = MessageSchema(
            subject='Confirm your email ',
            recipients=[email],
            template_body={
                           'subject': subject,
                           'host': host, 
                           'username': username, 
                           'token': token_verification,
                           },
            subtype=MessageType.html
            )

        fm = FastMail(conf)
        await fm.send_message(message, template_name='email_template.html')

    except ConnectionErrors as err:
        print(err)


async def send_reset_password(email: EmailStr, username: str, host: str):
    """Приймає три аргументи – адресу електронної пошти одержувача, ім’я користувача 
    і хост, де працює наш застосунок. Насамперед створюємо токен JWT для верифікації 
    запиту скидання пароля за допомогою методу auth_service.create_password_reset_token. Потім 
    цей токен передається в шаблон електронної пошти як змінна за допомогою 
    параметра template_body.
    (створюємо об’єкт MessageSchema із зазначеними темою, одержувачами та тілом шаблону, 
    а потім передаємо його об’єкту FastMail. Наприкінці викликаємо метод 
    send_message, 
    що передає повідомлення та ім’я шаблону password_reset.html. 
    Сам шаблон знаходиться в папці templates)
    """
    subject = 'Reset password '
    try:
        token_verification = await auth_service.create_password_reset_token({'sub': email})
        message = MessageSchema(
            subject='Reset password ',
            recipients=[email],
            template_body={
                           'subject': subject,
                           'host': host, 
                           'username': username, 
                           'token': token_verification,
                           },
            subtype=MessageType.html
            )

        fm = FastMail(conf)
        await fm.send_message(message, template_name='password_reset.html')
        
    except ConnectionErrors as err:
        print(err)
