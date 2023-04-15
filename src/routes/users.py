# дозволити користувачеві завантажувати свої аватари в нашому REST API. Для цього визначимо новий роутинг /api/users
import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, status, UploadFile, File
from sqlalchemy.orm import Session

from src.conf.config import settings
from src.database.db_connect import get_db
from src.database.models import User
from src.repository import users as repository_users
from src.schemes import UserDb
from src.services.auth import auth_service


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/", response_model=UserDb)
async def read_users_me(current_user: User = Depends(auth_service.get_current_user)):
    return current_user


@router.patch('/avatar', response_model=UserDb)
async def update_avatar_user(
                             file: UploadFile = File(), 
                             current_user: User = Depends(auth_service.get_current_user),
                             db: Session = Depends(get_db)
                             ):
    """For updating avatar."""
    # Функція cloudinary.config використовується для налаштування з’єднання з обліковим записом cloudinary
    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True
        )

    # завантаження файлу зображення, при цьому параметр public_id встановлюємо відповідно до імені поточного користувача та папки NotesApp
    cloudinary.uploader.upload(file.file, public_id=f'PVA_App/{current_user.username}', overwrite=True)
    src_url = (
               cloudinary
               .CloudinaryImage(f'PVA_App/{current_user.username}')
               .build_url(width=250, height=250, crop='fill')  # , version=r.get('version')
               )
    
    user = await repository_users.update_avatar(current_user.email, src_url, db)

    return user
