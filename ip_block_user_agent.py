import re
from typing import Callable

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

app = FastAPI()

user_agent_ban_list = [r"Gecko", r"Python-urllib"]


@app.middleware("http")
async def user_agent_ban_middleware(request: Request, call_next: Callable):
    user_agent = request.headers.get("user-agent")
    for ban_pattern in user_agent_ban_list:
        if re.search(ban_pattern, user_agent):
            return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": "You are banned"})
    response = await call_next(request)
    return response


@app.get("/")
def read_root():
    return {"message": "Hello world"}


"""
Бан User Agent
User-Agent (UA) – це рядок, який браузер надсилає на сервер у заголовку HTTP-запиту. 
Вона містить інформацію про браузер, операційну систему, версію та інші деталі. 
Сервер може використовувати цю інформацію для ідентифікації та аналізу клієнта, 
а також для сумісності зі старими браузерами або для визначення мобільних пристроїв.

Для бану на основі рядка User Agent можна використовувати 
регулярні вирази для перевірки відповідності рядка User Agent заблокованим значенням.

функція проміжного ПЗ user_agent_ban_middleware перевіряє заголовок "user-agent" вхідних запитів 
на відповідність списку заборонених рядків користувацьких агентів, 
що зберігаються в user_agent_ban_list. Якщо рядок агента користувача відповідає будь-якому 
із заборонених шаблонів, проміжне ПЗ повертає JSON-відповідь з кодом 
статусу HTTP 403 (Forbidden) та повідомленням "You are banned".

Якщо рядок агента користувача не заборонений, проміжне ПЗ викликає наступну функцію 
проміжного ПЗ або обробник кінцевої точки (в цьому випадку read_root) 
для продовження обробки запиту та повертає свою відповідь.
"""
