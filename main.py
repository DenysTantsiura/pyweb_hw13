# FastAPI + REST API example (Contacts) + Authorization + ...

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi_limiter.depends import FastAPILimiter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates  # poetry add jinja2
import redis.asyncio as redis
from sqlalchemy.orm import Session
from sqlalchemy import text
import uvicorn
from starlette.templating import _TemplateResponse

from src.database.db_connect import get_db
from src.routes import auth, contacts, users

from src.conf.config import settings


# export PYTHONPATH="${PYTHONPATH}:/1prj/pyweb_hw13/"
app = FastAPI()

# Add CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(','),  # defines the list of sources that are allowed to access the app
    # True  - means that credential-aware cross-domain requests are allowed:
    allow_credentials=True if settings.cors_credentials in ('y', 'yes', 'True', 'true', 'on', '1') else False,  
    allow_methods=settings.cors_methods.split(','),  # allowed HTTP methods, for cross-domain requests
    allow_headers=settings.cors_headers.split(','),  # allowed HTTP headers, for cross-domain requests
    )

app.include_router(auth.router, prefix='/api')
app.include_router(contacts.router, prefix='/api')
app.include_router(users.router, prefix='/api')


templates = Jinja2Templates(directory='templates')
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def startup():
    """
    The startup function is called when the application starts up.
    It's used to initialize Redis, which allows us to use Redis for rate limiting.

    :return: A client object, which is then passed to the fastapi limiter
    :doc-author: Trelent
    """
    client = await redis.Redis(
                               host=settings.redis_host,
                               port=settings.redis_port,
                               password=settings.redis_password,
                               db=0, 
                               encoding="utf-8",
                               decode_responses=True
                               )
    
    # is used to initialize a connection to Redis, enabling Redis to store rate-limiting information:
    await FastAPILimiter.init(client)


@app.get('/', response_class=HTMLResponse, description='Main Page')
async def root(request: Request) -> _TemplateResponse:
    """
    The root function is the entry point for the application.
    It returns a simple HTML page with a title and message.

    :param request: Request: Get information about the request that comes to the server
    :return: A response object (HTMLResponse ? _TemplateResponse)
    :doc-author: Trelent
    """
    return templates.TemplateResponse('index.html', {'request': request, 'title': 'The personal virtual assistant...'})
    # return {' Welcome! ': ' The personal virtual assistant is ready to go, I`m kidding ^_^ '}


@app.get('/api/healthchecker')
def healthchecker(db: Session = Depends(get_db)) -> dict:
    """
    Check if the container (DB server) is up.
    The healthchecker function is a simple function that checks if the database connection is working.
    It does this by executing a SQL query to fetch one row from the database and then checking if it was successful.
    If it was not successful, an HTTPException will be raised with status code 500 (Internal Server Error) and detail
    message 'Error connecting to the database!'.
    Otherwise, we return a dictionary with key 'ALERT' and value 'Welcome to FastAPI! System ready!'.

    :param db: Session: Pass the database session to the function
    :return: A dict with the key 'alert' and value 'welcome to fastapi! system ready!' (? JSONResponse)
    :doc-author: Trelent
    """
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
