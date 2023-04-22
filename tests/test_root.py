
from fastapi.templating import Jinja2Templates 
from fastapi.testclient import TestClient
# import pytest

import main


client = TestClient(main.app)
templates = Jinja2Templates(directory='templates')


def test_root():
    response = client.get('/')
    assert response.status_code == 200  # status.HTTP_200_OK 
    assert response.template.name == 'index.html'
    assert "request" in response.context


def test_healthchecker():
    response = client.get('/api/healthchecker')
    assert response.status_code == 200
    assert response.json() == {'ALERT': 'Welcome to FastAPI! System ready!'}
