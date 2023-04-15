import redis.asyncio as redis
import uvicorn
from fastapi import Depends, FastAPI

from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter


app = FastAPI()


@app.on_event("startup")
async def startup():
    """
    На старті застосунку @app.on_event("startup") метод FastAPILimiter.init використовується 
    для ініціалізації з’єднання з Redis. Це дає змогу використовувати Redis 
    для зберігання інформації про обмеження швидкості.
    """
    r = await redis.Redis(host='localhost', port=6379, db=0, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(r)


@app.get("/", dependencies=[Depends(RateLimiter(times=2, seconds=5))])
async def index():
    """
    Залежність RateLimiter використовується для встановлення обмеження швидкості для маршруту "/". 
    Обмеження швидкості встановлено на 2 запити за 5 секунд. Це означає, що користувач може зробити 
    лише 2 запити до цього маршруту протягом 5 секунд. 
    Якщо користувач перевищить цей ліміт, він отримає відповідь 429 Too Many Requests.
    """
    return {"msg": "Hello World"}


if __name__ == "__main__":
    uvicorn.run("app:app", reload=True)
