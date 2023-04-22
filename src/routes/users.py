# import cloudinary
# import cloudinary.uploader
from fastapi import APIRouter, Depends, UploadFile, File  # status
from sqlalchemy.orm import Session

# from src.conf.config import settings
from src.database.db_connect import get_db
from src.database.models import User
from src.repository import users as repository_users
from src.schemes import UserDb
from src.services.auth import auth_service
from src.services.avatar_uploads import avatar_upload


router = APIRouter(prefix='/users', tags=['users'])


@router.get('/me/', response_model=UserDb)
async def read_users_me(current_user: User = Depends(auth_service.get_current_user)) -> User:
    """
    The read_users_me function is a GET endpoint that returns the current user's information.
    It uses the auth_service to get the current user, and then returns it.

    :param current_user: User: Get the current user
    :return: The current user
    :doc-author: Trelent
    """
    return current_user


@router.patch('/avatar', response_model=UserDb)
async def update_avatar_user(
                             file: UploadFile = File(), 
                             current_user: User = Depends(auth_service.get_current_user),
                             db: Session = Depends(get_db)
                             ) -> User:
    """
    The update_avatar_user function is used to update the avatar of a user.

    :param file: UploadFile: Upload the image file
    :param current_user: User: Get the current user from the database
    :param db: Session: Access the database
    :return: A user object with the updated avatar_url field
    :doc-author: Trelent
    """
    # # The cloudinary.config function is used to configure the connection to the cloudinary account
    # cloudinary.config(
    #     cloud_name=settings.cloudinary_name,
    #     api_key=settings.cloudinary_api_key,
    #     api_secret=settings.cloudinary_api_secret,
    #     secure=True
    #     )

    # # the public_id parameter is set according to the name of the current user and the PVA_App folder:
    # cloudinary.uploader.upload(file.file, public_id=f'PVA_App/{current_user.username}', overwrite=True)
    # src_url = (
    #            cloudinary
    #            .CloudinaryImage(f'PVA_App/{current_user.username}')
    #            .build_url(width=250, height=250, crop='fill')  # , version=r.get('version')    r?
    #            )
    
    src_url = avatar_upload(file.file, f'{current_user.username}_id{current_user.id}')

    user = await repository_users.update_avatar(current_user.email, src_url, db)

    return user
