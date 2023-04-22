from typing import BinaryIO

import cloudinary
from cloudinary.api import resource as r

from src.conf.config import settings


# The cloudinary.config function is used to configure the connection to the cloudinary account
cloudinary.config(
                  cloud_name=settings.cloudinary_name,
                  api_key=settings.cloudinary_api_key,
                  api_secret=settings.cloudinary_api_secret,
                  secure=True
                  )

def avatar_upload(file: BinaryIO, user_name: str, crops: tuple[int, int] = (120, 120)) -> str:
    
    avatar_id = f'PVA_App/{user_name}'
    # the public_id parameter is set according to the name of the current user and the PVA_App folder:
    cloudinary.uploader.upload(file.file, public_id=avatar_id, overwrite=True)
    src_url = (
               cloudinary
               .CloudinaryImage(avatar_id)
               .build_url(width=crops[0], height=crops[1], crop='fill', version=r(avatar_id).get('version'))
               )

    return src_url
