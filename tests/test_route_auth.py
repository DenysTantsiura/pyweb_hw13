
import asyncio

from fastapi.templating import Jinja2Templates 
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from fastapi import status

from src.database.models import User
from src.routes import auth

from src.services.auth import auth_service
# client = TestClient(auth.app)
# templates = Jinja2Templates(directory='templates')
# print(f'!!!\n{response}\n!!!')

# client - from conftest.py, user - fixture from conftest.py, = common to all; monkeypatch -method to mock services
def test_signup_ok(client, user, monkeypatch):
    mock_send_email = MagicMock()
    # create mock for function where it`s call
    # not src.services.email, from import in route.auth
    monkeypatch.setattr('src.routes.auth.send_email', mock_send_email)  
    response = client.post('api/auth/signup', json=user)
    assert response.status_code == 201, response.text  # status.HTTP_201_CREATED
    data = response.json()
    assert data['user']['email'] == user.get('email')
    assert 'id' in data['user']


def test_signup_fail(client, user):  # , mocker
    # mocker.patch('src.routes.auth.send_email')  # !- background_tasks not execute
    response = client.post('api/auth/signup', json=user)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()['detail'] == 'Account already exists!'


def test_login_ok(client, session, user):
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()  # contact
    current_user.confirmed = True
    session.commit()

    response = client.post('api/auth/login', data={'username': user.get('email'), 'password': user.get('password')})
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data['token_type'] == 'bearer'
    

def test_login_fail(client, session, user):  # split into several?
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user.confirmed = False
    session.commit()
    
    response1 = client.post('api/auth/login', data={'username': 'NonExistUser', 'password': user.get('password')})
    assert response1.status_code == status.HTTP_401_UNAUTHORIZED
    assert response1.json()['detail'] == 'Invalid email'

    response2 = client.post('api/auth/login', data={'username': user.get('email'), 'password': user.get('password')})
    assert response2.status_code == status.HTTP_401_UNAUTHORIZED
    assert response2.json()['detail'] == 'Email not confirmed'

    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user.confirmed = True
    session.commit()

    response3 = client.post('api/auth/login', data={'username': user.get('email'), 'password': '54327'})
    assert response3.status_code == status.HTTP_401_UNAUTHORIZED
    assert response3.json()['detail'] == 'Invalid password'


def test_refresh_token_ok(client, session, user):
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()

    headers = {'Authorization': f'Bearer {current_user.refresh_token}'}
    response = client.get('api/auth/refresh_token', headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['token_type'] == 'bearer'
    assert response.json()['access_token'] is not None
    assert response.json()['refresh_token'] is not None
  

def test_refresh_token_fail(client, user):
    headers = {'Authorization': f'Bearer NOTOKEN'}
    response = client.get('api/auth/refresh_token', headers=headers)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()['detail'] == 'Could not validate credentials'  # why not 'Invalid refresh token'?  need mock?
    # or check invalid token?

    invalid_refresh_token = asyncio.run(
        auth_service.create_refresh_token(data={'sub': user['email']}, expires_delta=10)
    )
    headers = {'Authorization': f'Bearer {invalid_refresh_token}'}
    response = client.get('api/auth/refresh_token', headers=headers)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()['detail'] == 'Invalid refresh token'


def test_confirmed_email_ok(client, session, user):
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user.confirmed = False
    session.commit()

    email_token = auth_service.create_email_token(data={'sub': user['email'], 'email': user['email'], 'username': user['username']})
    response = client.get(f'api/auth/confirmed_email/{email_token}')

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['message'] == 'Email confirmed'

    '''
    def test_confirmed_email_was_successfully(self, client, session, user,
                                              detail, is_confirmed):
        if is_confirmed:
            db_user = session.scalar(select(User).filter(User.email == user['email']))
            db_user.confirmed = False
            session.commit()

        email_token = asyncio.run(
            auth_service.create_email_token(data={'sub': user['email']})
        )
        response = client.get(self.url_path.format(token=email_token))

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['message'] == detail
    '''

def test_confirmed_email_fail(client, session, user):
    pass

def test_confirmed_email_done(client, user, monkeypatch):
    pass

def test_request_email_ok(client, user, monkeypatch):
    pass

def test_request_email_check(client, user, monkeypatch):
    pass

def test_reset_password_ok(client, user, monkeypatch):
    pass

def test_reset_password_check(client, user, monkeypatch):
    pass

def test_reset_password_not_ready(client, user, monkeypatch):
    pass


def test_reset_password_done(client, user, monkeypatch):
    pass


def test_reset_password_confirm_ok(client, user, monkeypatch):
    pass

def test_reset_password_confirm_fail(client, user, monkeypatch):
    pass


def test_reset_password_complete_ok(client, user, monkeypatch):
    pass


'''
def test_create_user(client, user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr('src.routes.auth.send_email', mock_send_email)
    response = client.post(
        '/api/auth/signup',
        json=user,
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data['user']['email'] == user.get('email')
    assert 'id' in data['user']


def test_repeat_create_user(client, user):
    response = client.post(
        "/api/auth/signup",
        json=user,
    )
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == "Account already exists"


def test_login_user_not_confirmed(client, user):
    response = client.post(
        "/api/auth/login",
        data={"username": user.get('email'), "password": user.get('password')},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Email not confirmed"


def test_login_user(client, session, user):
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user.confirmed = True
    session.commit()
    response = client.post(
        "/api/auth/login",
        data={"username": user.get('email'), "password": user.get('password')},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, user):
    response = client.post(
        "/api/auth/login",
        data={"username": user.get('email'), "password": 'password'},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid password"


def test_login_wrong_email(client, user):
    response = client.post(
        "/api/auth/login",
        data={"username": 'email', "password": user.get('password')},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid email"
    '''