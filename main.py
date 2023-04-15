# FastAPI + REST API example (Contacts) + Authorization + ...

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi_limiter.depends import FastAPILimiter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates  # !!! poetry add jinja2
import redis.asyncio as redis
from sqlalchemy.orm import Session
from sqlalchemy import text
import uvicorn

from src.database.db_connect import get_db
from src.routes import auth, contacts, users

from src.conf.config import settings


app = FastAPI()

# Add CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(','),  # визначає список джерел, яким дозволено доступ до застосунку
    # True означає, що дозволені кросдоменні запити з урахуванням облікових даних:
    allow_credentials=True if settings.cors_credentials in ('y', 'yes', 'True', 'true', 'on', '1') else False,  
    allow_methods=settings.cors_methods.split(','),  # дозволені методи HTTP, для кросдоменних запитів
    allow_headers=settings.cors_headers.split(','),  # дозволені заголовки HTTP, для кросдоменних запитів
    )

app.include_router(auth.router, prefix='/api')
app.include_router(contacts.router, prefix='/api')
app.include_router(users.router, prefix='/api')


templates = Jinja2Templates(directory='templates')
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def startup():
    client = await redis.Redis(
                               host=settings.redis_host,
                               port=settings.redis_port,
                               password=settings.redis_password,
                               db=0, 
                               encoding="utf-8",
                               decode_responses=True
                               )
    
    # використовується для ініціалізації з’єднання з Redis, що дає змогу використовувати Redis 
    # для зберігання інформації про обмеження швидкості:
    await FastAPILimiter.init(client)


@app.get('/', response_class=HTMLResponse, description='Main Page')
async def root(request: Request) -> HTMLResponse:  # _TemplateResponse ?
    # return {' Welcome! ': ' The personal virtual assistant is ready to go, I`m kidding ^_^ '}
    return templates.TemplateResponse('index.html', {'request': request, 'title': 'The personal virtual assistant...'})


@app.get('/api/healthchecker')
def healthchecker(db: Session = Depends(get_db)) -> dict:  # JSONResponse ?
    """Check if the container (DB server) is up."""
    try:
        result = db.execute(text('SELECT 1')).fetchone()
        if result is None:
            raise HTTPException(status_code=500, detail='Database is not configured correctly!')
        
        return {'ALERT': 'Welcome to FastAPI! System ready!'}
    
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail='Error connecting to the database!')


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
