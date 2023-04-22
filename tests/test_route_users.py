from fastapi import status
import pytest
from sqlalchemy import select

from src.database.models import User


@pytest.fixture(scope='function')
def access_token(client, user, session, mocker) -> str:
    mocker.patch('src.routes.auth.send_email')

    client.post('/api/auth/signup', json=user)

    current_user: User = session.scalar(select(User).filter(User.email == user['email']))
    current_user.confirmed = True
    session.commit()

    response = client.post(
                           '/api/auth/login',
                           data={'username': user.get('email'), 'password': user.get('password')},
                           )
    return response.json()['access_token']


def test_read_users_me(client, access_token):
    response = client.get('api/users/me/')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('api/users/me/', headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert 'id' in response.json()
    assert 'username' in response.json()
    assert 'email' in response.json()
    assert 'created_at' in response.json()
    assert 'avatar' in response.json()
  

def test_update_avatar_user(client, user, access_token, mocker):
    mock_avatar = 'https://pypi.org/static/images/logo-small.2a411bc6.svg'
    mocker.patch('src.routes.users.avatar_upload', return_value=mock_avatar)
    files = {'file': 'avatar_1.svg'}

    response = client.patch('api/users/avatar', files=files)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.patch('api/users/avatar', headers=headers, files=files)
    assert response.status_code == status.HTTP_200_OK
    assert 'id' in response.json()
    assert 'username' in response.json()
    assert 'email' in response.json()
    assert 'created_at' in response.json()
    assert 'avatar' in response.json()
    assert response.json()['email'] == user['email']
    assert response.json()['avatar'] == mock_avatar
    