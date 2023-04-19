# Схеми для валідації вхідних та вихідних даних
from datetime import date, datetime
from pydantic import BaseModel, Field, EmailStr  # poetry add pydantic[email] 


class ContactModel(BaseModel):
    """Contact model class."""
    name: str = Field(default='Unknown', min_length=2, max_length=30)
    last_name: str = Field(default='Unknown', min_length=2, max_length=40)
    email: EmailStr  # str =  Field(default='Unknown@mail.com', min_length=6, max_length=30, regex=...)  # i@i.ua
    phone: int = Field(default=1, gt=0, le=9999999999)
    birthday: date  # = Field(default=date.today())  # YYYY-MM-DD
    description: str = Field(default='-', max_length=3000)  # String


class ContactResponse(ContactModel):
    """Class for contact response."""
    id: int = 1 

    class Config:
        """Indicates that the ContactResponse model is used to represent the ORM model."""
        orm_mode = True


class CatToNameModel(BaseModel):
    """Class Category to Name model."""
    name: str = Field(default='Unknown-next', min_length=2, max_length=30)


class UserModel(BaseModel):
    """User model class."""
    username: str = Field(min_length=2, max_length=30)
    email: EmailStr  # str
    password: str = Field(min_length=6, max_length=10)


class UserDb(BaseModel):
    """Class User for DataBase."""
    id: int
    username: str
    email: str
    created_at: datetime
    avatar: str

    class Config:
        """Indicates that the UserDb model is used to represent the ORM model."""
        orm_mode = True


class UserResponse(BaseModel):
    """User response class."""
    user: UserDb
    detail: str = 'User successfully created'


class TokenModel(BaseModel):
    """Defines the response when receiving access tokens for an authenticated user."""
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'


class RequestEmail(BaseModel):
    """Request Email class."""
    email: EmailStr


class PasswordRecovery(BaseModel):
    """To check the sufficiency of the password during the password recovery procedure."""
    password: str = Field(min_length=6, max_length=10)
