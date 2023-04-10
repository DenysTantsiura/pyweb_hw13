# FastAPI + REST API example (Contacts) + Authorization
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import uvicorn

from src.database.db_connect import get_db
from src.routes import auth, contacts


app = FastAPI()

app.include_router(auth.router, prefix='/api')
app.include_router(contacts.router, prefix='/api')


@app.get("/")
async def root() -> dict:
    return {" Welcome! ": " The personal virtual assistant is ready to go, I'm kidding ^_^ "}


@app.get("/api/healthchecker")
def healthchecker(db: Session = Depends(get_db)) -> dict: 
    """Check if the container (DB server) is up."""
    try:
        result = db.execute(text("SELECT 1")).fetchone()
        if result is None:
            raise HTTPException(status_code=500, detail="Database is not configured correctly!")
        
        return {"ALERT": "Welcome to FastAPI! System ready!"}
    
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error connecting to the database!")


if __name__ == "__main__":
    uvicorn.run(app, host='127.0.0.1', port=8001)
