# FastAPI + REST API example (Contacts) + Authorization
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates  # !!! poetry add jinja2
from sqlalchemy.orm import Session
from sqlalchemy import text
import uvicorn

from src.database.db_connect import get_db  # tl13_2.
from src.routes import auth, contacts


app = FastAPI()

app.include_router(auth.router, prefix='/api')
app.include_router(contacts.router, prefix='/api')


templates = Jinja2Templates(directory='templates')
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get('/', response_class=HTMLResponse, description='Main Page')
async def root(request: Request) -> HTMLResponse:
    # return {' Welcome! ': ' The personal virtual assistant is ready to go, I`m kidding ^_^ '}
    return templates.TemplateResponse('index.html', {'request': request, 'title': 'The personal virtual assistant'})


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
