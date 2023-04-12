from pathlib import Path

import uvicorn
from fastapi import FastAPI, BackgroundTasks  # https://fastapi.tiangolo.com/tutorial/background-tasks/
"""Клас BackgroundTasks дозволяє виконувати тривалі завдання, такі як надсилання електронної пошти або 
обробка зображень, у фоновому режимі, щоб ваш API міг продовжувати обробляти інші запити. Це особливо 
корисно для завдань, виконання яких може зайняти багато часу і, в іншому разі, API не зможе 
відповідати на інші запити."""
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr, BaseModel
from typing import List

from authentication import get_password


class EmailSchema(BaseModel):
    email: EmailStr


conf = ConnectionConfig(
    MAIL_USERNAME=get_password('metamail.txt'),  # "usernamep@meta.ua",
    MAIL_PASSWORD=get_password('metakey.txt'),  # "secretPassword",
    MAIL_FROM=get_password('metamail.txt'),  # "example@meta.ua",
    MAIL_PORT=465,
    MAIL_SERVER='smtp.meta.ua',
    MAIL_FROM_NAME='Example email',
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent / 'templates',  # here example_email.html
    )

app = FastAPI()


@app.post('/send-email')  # Клас EmailSchema визначає очікувану структуру корисного навантаження для надсилання email
async def send_in_background(background_tasks: BackgroundTasks, body: EmailSchema):
    """Маршрут /send-email приймає адресу електронної пошти у вигляді корисного навантаження JSON 
    і надсилає електронні листи як фонове завдання."""
    # створює об’єкт повідомлення
    message = MessageSchema(
        subject='Fastapi mail module',
        recipients=[body.email],
        template_body={'fullname': 'Billy Jones'},  # передача необхідних даних всередину шаблону листа
        subtype=MessageType.html
        )

    # Клас FastMail ініціалізується об’єктом ConnectionConfig, який визначає конфігурацію для підключення до сервера 
    # електронної пошти, наприклад, адресу сервера MAIL_SERVER="smtp.meta.ua", 
    # порт MAIL_PORT=465 та 
    # інформацію про аутентифікацію MAIL_USERNAME="example@meta.ua", MAIL_PASSWORD="secretPassword"
    fm = FastMail(conf)

    # Саме надсилання листа здійснюється за допомогою класу BackgroundTasks як фонове завдання
    background_tasks.add_task(fm.send_message, message, template_name='example_email.html')  # look at line 25
    
    # Функція повертає відповідь у форматі JSON, яка вказує на те, що лист був надісланий; 
    # Хоча саме надсилання може виконуватися ще й у фоновому режимі:
    return {'message': 'email has been sent'}


if __name__ == '__main__':
    uvicorn.run('main:app', port=8000, reload=True)
    """main:app вказує uvicorn, модуль – це файл main.py та 
    об’єкт програми всередині коду app, який необхідно запустити;
    port=8000 визначає номер порту для прослуховування;
    reload=True дає змогу автоматично перезавантажувати застосунок у разі зміни коду;"""
