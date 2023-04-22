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
    """
    The send_email function sends an email to the user's email address.
        Args:
            email (str): The user's email address.
            username (str): The username of the user who is registering for a new account.

    :param email: EmailStr: Validate the email address
    :param username: str: Pass the username of the user who is registering
    :param host: str: Pass the host name of the server to be used in the email template
    :return: A coroutine, which is an object that can be awaited
    :doc-author: Trelent
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
    """
    The send_reset_password function sends a password reset email to the user.
        Args:
            email (str): The user's email address.
            username (str): The user's username.  This is used in the template for personalization purposes only, and
            is not required by this function or any other part of the application.
            host (str): The hostname of your website, e.g., 'http://localhost:8000'.  This is used in the template
            for personalization purposes only, and is not required by this function or any other part
            of the application.

    :param email: EmailStr: Get the email address of the user
    :param username: str: Get the username of the user who is requesting a password reset
    :param host: str: Create the link to reset the password
    :return: A token
    :doc-author: Trelent
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
