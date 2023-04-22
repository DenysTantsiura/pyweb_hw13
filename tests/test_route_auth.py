
import asyncio

from unittest.mock import MagicMock
from fastapi import status

from src.conf import messages as m
from src.database.models import User
from src.routes import auth  # redundand
from src.services.auth import auth_service


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
    assert response.json()['detail'] == m.ACCOUNT_EXIST


def test_login_ok(client, session, user):
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()  # contact
    current_user.confirmed = True
    session.commit()

    response = client.post('api/auth/login', data={'username': user.get('email'), 'password': user.get('password')})
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data['token_type'] == 'bearer'  # m.TOKEN_TYPE
    

def test_login_fail(client, session, user):  # split into several?
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user.confirmed = False
    session.commit()
    
    response1 = client.post('api/auth/login', data={'username': 'NonExistUser', 'password': user.get('password')})
    assert response1.status_code == status.HTTP_401_UNAUTHORIZED
    assert response1.json()['detail'] == m.INCORRECT_MAIL

    response2 = client.post('api/auth/login', data={'username': user.get('email'), 'password': user.get('password')})
    assert response2.status_code == status.HTTP_401_UNAUTHORIZED
    assert response2.json()['detail'] == m.UNCOMFIRMED_EMAIL

    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user.confirmed = True
    session.commit()

    response3 = client.post('api/auth/login', data={'username': user.get('email'), 'password': '54327'})
    assert response3.status_code == status.HTTP_401_UNAUTHORIZED
    assert response3.json()['detail'] == m.INCORRECT_PASSWORD


def test_refresh_token_ok(client, session, user):
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()

    headers = {'Authorization': f'Bearer {current_user.refresh_token}'}
    response = client.get('api/auth/refresh_token', headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['token_type'] == 'bearer'  # m.TOKEN_TYPE
    assert response.json()['access_token'] is not None
    assert response.json()['refresh_token'] is not None
  

def test_refresh_token_fail(client, user):
    headers = {'Authorization': f'Bearer NOTOKEN'}
    response = client.get('api/auth/refresh_token', headers=headers)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()['detail'] == m.INCORRECT_CREDENTIALS  
    # why not 'Invalid refresh token'?  need mock? or check untrue(invalid) token?

    untrue_refresh_token = asyncio.run(
                                        auth_service.create_refresh_token(data={'sub': user['email']}, expires_delta=10)
                                        )
    headers = {'Authorization': f'Bearer {untrue_refresh_token}'}
    response = client.get('api/auth/refresh_token', headers=headers)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()['detail'] == m.INCORRECT_REFRESH_TOKEN


def test_confirmed_email_ok(client, session, user):
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user.confirmed = False
    session.commit()

    email_token = auth_service.create_email_token(
                                                  data={
                                                        'sub': user['email'],
                                                        'email': user['email'],
                                                        'username': user['username'],
                                                         }
                                                  )
    response = client.get(f'api/auth/confirmed_email/{email_token}')

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['message'] == m.CONFIRMED_EMAIL


def test_confirmed_email_fail(client, session, user):  # split into several?
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user.confirmed = True
    session.commit()

    email_token = auth_service.create_email_token(
                                                  data={
                                                        'sub': user['email'],
                                                        'email': user['email'],
                                                        'username': user['username'],
                                                        }
                                                  )
    response = client.get(f'api/auth/confirmed_email/{email_token}')

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['message'] == m.CONFIRMED_EMAIL_ALREADY

    email_token = auth_service.create_email_token(data={'sub': 'UNKNOWN!@com.com', 'email': '-', 'username': '-'})
    response = client.get(f'api/auth/confirmed_email/{email_token}')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == m.ERROR_VERIFICATION


def test_request_email_ok(client, session, user):
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user.confirmed = True
    session.commit()

    response = client.post('api/auth/request_email', json={'email': user.get('email')})

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['message'] == m.CONFIRMED_EMAIL_ALREADY


def test_request_email_check(client, session, user):  # , monkeypatch is redundant
    # mock_send_email = MagicMock() # redundant
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user.confirmed = False
    session.commit()

    # monkeypatch.setattr('src.routes.auth.send_email', mock_send_email)  # redundant
    
    response = client.post('api/auth/request_email', json={'email': user.get('email')})

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['message'] == m.WARNING_EMAIL

    response2 = client.post('api/auth/request_email', json={'email': 'Email@notSignUp.user'})

    assert response2.status_code == status.HTTP_200_OK
    assert response2.json()['message'] == m.WARNING_EMAIL


def test_reset_password_ok(client, session, user):
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user.confirmed = True
    session.commit()

    response = client.post('api/auth/reset-password', json={'email': user.get('email')})

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['message'] == m.WARNING_EMAIL


def test_reset_password_check(client, session, user):  # split into several?
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user.confirmed = False
    session.commit()

    response = client.post('api/auth/reset-password', json={'email': user.get('email')})

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['message'] == m.WARNING_VERIFIED_EMAIL

    response2 = client.post('api/auth/reset-password', json={'email': 'Non_exist@email.com'})

    assert response2.status_code == status.HTTP_200_OK
    assert response2.json()['message'] == m.WARNING_ATTENTION_EMAIL


def test_reset_password_done(client):
    response = client.get('api/auth/reset-password/done')

    assert response.status_code == status.HTTP_200_OK
    assert response.template.name == 'password_reset_done.html'
    assert 'request' in response.context
    assert 'title' in response.context
    assert response.context['title'] == m.MSG_SENT_PASSWORD


def test_reset_password_confirm_ok(client, session, user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr('src.routes.auth.send_email', mock_send_email) 

    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user.confirmed = True
    session.commit()

    user.update(password='new_secret')

    token = auth_service.create_email_token(data={'sub': user['email']})

    response = client.post(f'api/auth/reset-password/confirm/{token}', json={'password': user['password']})
 
    assert response.status_code == status.HTTP_200_OK
    assert 'user' in response.json()  # response.content  # context
    assert response.json()['detail'] == m.MSG_PASSWORD_CHENGED


def test_reset_password_confirm_fail(client, session, user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr('src.routes.auth.send_email', mock_send_email) 

    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user.confirmed = True
    session.commit()

    token = auth_service.create_email_token(data={'sub': 'Non_exist@user.mail'})
    response = client.post(f'api/auth/reset-password/confirm/{token}', json={'password': 'new_secret'})  # data=   json=

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json()['detail'] == m.WARNING_INVALID_TOKEN


def test_reset_password_complete_ok(client):
    response = client.get('api/auth/reset-password/complete')

    assert response.status_code == status.HTTP_200_OK
    assert response.template.name == 'password_reset_complete.html'
    assert 'request' in response.context
    assert 'title' in response.context
    assert response.context['title'] == m.MSG_PASSWORD_RESET
