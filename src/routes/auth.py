from fastapi import APIRouter, HTTPException, Depends, status, Security, BackgroundTasks, Request
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from fastapi.templating import Jinja2Templates
from starlette.templating import _TemplateResponse
from sqlalchemy.orm import Session

from src.database.db_connect import get_db
from src.repository import users as repository_users
from src.schemes import (
                         PasswordRecovery,
                         RequestEmail,
                         TokenModel,
                         UserModel, 
                         UserResponse,                       
                        )
from src.services.auth import auth_service
from src.services.email import send_email, send_reset_password


router = APIRouter(prefix='/auth', tags=['auth'])
security = HTTPBearer()

templates = Jinja2Templates(directory='src/services/templates')


@router.post('/signup', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
                 body: UserModel,
                 background_tasks: BackgroundTasks, 
                 request: Request, 
                 db: Session = Depends(get_db)
                 ) -> dict:
    """
    The signup function creates a new user in the database.

    :param body: UserModel: Get the user data from the request body
    :param background_tasks: BackgroundTasks: Add a background task to the list of tasks
    :param request: Request: Access the request object
    :param db: Session: Pass the database session to the function
    :return: A dictionary with two keys: user and detail
    :doc-author: Trelent
    """
    exist_user = await repository_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Account already exists!')
    
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db)
    # We create a background task of sending a letter:
    background_tasks.add_task(send_email, new_user.email, new_user.username, request.base_url)

    return {'user': new_user, 'detail': 'User successfully created'}


@router.post('/login', response_model=TokenModel)
async def login(
                body: OAuth2PasswordRequestForm = Depends(),  # OAuth2PasswordRequestForm automatically goes to Depends
                db: Session = Depends(get_db)
                ) -> dict:
    """
    The login function is used to authenticate a user.

    :param body: OAuth2PasswordRequestForm: Get the username and password from the request body
    :param db: Session: Access the database
    :return: A dict with the access_token, refresh_token and token_type
    :doc-author: Trelent
    """
    user = await repository_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid email')
    
    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Email not confirmed')
    
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid password')
    
    # Generate JWT
    access_token = await auth_service.create_access_token(data={'sub': user.email})
    refresh_token = await auth_service.create_refresh_token(data={'sub': user.email})
    await repository_users.update_token(user, refresh_token, db)

    return {'access_token': access_token, 'refresh_token': refresh_token, 'token_type': 'bearer'}


@router.get('/refresh_token', response_model=TokenModel)
async def refresh_token(
                        credentials: HTTPAuthorizationCredentials = Security(security), 
                        db: Session = Depends(get_db)
                        ) -> dict:
    """
    The refresh_token function is used to refresh the access token.
        The function takes in a refresh token and returns an access token,
        a new refresh token, and the type of authentication being used.

    :param credentials: HTTPAuthorizationCredentials: Get the token from the header of the request
    :param db: Session: Get the database session
    :return: The access_token and refresh_token,
    :doc-author: Trelent
    """
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repository_users.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid refresh token')

    access_token = await auth_service.create_access_token(data={'sub': email})
    refresh_token = await auth_service.create_refresh_token(data={'sub': email})
    await repository_users.update_token(user, refresh_token, db)

    return {'access_token': access_token, 'refresh_token': refresh_token, 'token_type': 'bearer'}


@router.get('/confirmed_email/{token}')
async def confirmed_email(
                          token: str, 
                          db: Session = Depends(get_db)
                          ) -> dict:
    """
    The confirmed_email function is used to confirm the user's email.
        The function takes a token as an argument and returns a message that the email has been confirmed or that it was already confirmed.


    :param token: str: Get the token from the url
    :param db: Session: Pass the database session to the function
    :return: A dict with a message
    :doc-author: Trelent
    """
    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Verification error')
     
    if user.confirmed:
        return {'message': 'Your email is already confirmed'}
    
    await repository_users.confirmed_email(email, db)

    return {'message': 'Email confirmed'}


@router.post('/request_email')
async def request_email(
                        body: RequestEmail, 
                        background_tasks: BackgroundTasks, 
                        request: Request,
                        db: Session = Depends(get_db)
                        ) -> dict:
    """
    The request_email function is used to send a confirmation email to the user.

    :param body: RequestEmail: Get the email from the request body
    :param background_tasks: BackgroundTasks: Add a task to the background queue
    :param request: Request: Get the base url of our application
    :param db: Session: Get the database session
    :return: A dictionary with a message
    :doc-author: Trelent
    """
    user = await repository_users.get_user_by_email(body.email, db)

    if user.confirmed:
        return {'message': 'Your email is already confirmed'}
    
    if user:
        background_tasks.add_task(send_email, user.email, user.username, request.base_url)

    return {'message': 'Check your email for confirmation.'}


@router.post('/reset-password')
async def reset_password(
                         body: RequestEmail, 
                         background_tasks: BackgroundTasks, 
                         request: Request,
                         db: Session = Depends(get_db)
                         ) -> dict:
    """
    The reset_password function is used to reset a user's password.
        It takes in the email address of the user and sends an email with a link to reset their password.
        The function returns a message indicating whether or not the request was successful.

    :param body: RequestEmail: Get the email from the request body
    :param background_tasks: BackgroundTasks: Add the task to the background tasks queue
    :param request: Request: Get the base url of the application
    :param db: Session: Access the database
    :return: A message to the user
    :doc-author: Trelent
    """
    user = await repository_users.get_user_by_email(body.email, db)

    if user and user.confirmed:
        background_tasks.add_task(send_reset_password, user.email, user.username, request.base_url)

        return {'message': 'Check your email for confirmation.'}
    
    if user:
        return {'message': 'Your email address has not been verified yet.'}
    
    return {'message': 'Check if the email is entered correctly.'}


# users/password_reset_done.html
@router.get('/reset-password/done', response_class=HTMLResponse, description='Request password reset Page')  
async def reset_password_done(request: Request) -> _TemplateResponse:
    """
    The reset_password_done function is called when the user clicks on the link in their email.
    It displays a message to let them know that an email has been sent with instructions for resetting
    their password.

    :param request: Request: Access the request object
    :return: A template response object (HTMLResponse ? _TemplateResponse)
    :doc-author: Trelent
    """
    return templates.TemplateResponse('password_reset_done.html', {'request': request,
                                                                   'title': 'Password-change email has been sent'})


@router.post('/reset-password/confirm/{token}')
async def reset_password_confirm(
                                 body: PasswordRecovery,
                                 background_tasks: BackgroundTasks, 
                                 request: Request,
                                 token: str,
                                 db: Session = Depends(get_db)
                                 ) -> dict:
    """
    The reset_password_confirm function is used to reset a user's password.
        It takes the following parameters:
            body (PasswordRecovery): The new password for the user.
            background_tasks (BackgroundTasks): A BackgroundTasks object that allows us to add tasks to be run
            in the background.
            We will use this object to send an email notification when a user's
            password has been changed successfully.
            This parameter is automatically injected by FastAPI, so we don't need
            to pass it explicitly when calling this function from our code or
            tests later on.

    :param body: PasswordRecovery: Get the password from the request body
    :param background_tasks: BackgroundTasks: Create a background task
    :param request: Request: Get the base url of the application
    :param token: str: Get the token from the url
    :param db: Session: Access the database
    :return: The following json response:
    :doc-author: Trelent
    """
    email = await auth_service.get_email_from_token(token)
    exist_user = await repository_users.get_user_by_email(email, db)
    if not exist_user:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail='Can`t find user by email from token.')
    
    body.password = auth_service.get_password_hash(body.password)
    
    updated_user = await repository_users.change_password_for_user(exist_user, body.password, db)
    if updated_user is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail='Can`t find user by email from token.')

    # request.base_url ->  http://127.0.0.1:8000/
    background_tasks.add_task(send_email, updated_user.email, updated_user.username, request.base_url)  

    return {'user': updated_user, 'detail': 'User`s password successfully changed.'}


# users/password_reset_complete.html
@router.get('/reset-password/complete', response_class=HTMLResponse, description='Complete password reset Page')  
async def reset_password_complete(request: Request) -> _TemplateResponse:
    """
    The reset_password_complete function is called when the user has successfully reset their password.
    It renders a template that informs the user of this fact.

    :param request: Request: Get the current request object
    :return: A template response object (HTMLResponse ? _TemplateResponse)
    :doc-author: Trelent
    """
    return templates.TemplateResponse('password_reset_complete.html', {'request': request,
                                                                       'title': 'Complete password reset'})
