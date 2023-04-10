# Схеми для валідації вхідних та вихідних даних
from datetime import date, datetime
from pydantic import BaseModel, Field, EmailStr  # poetry add pydantic[email] 


class ContactModel(BaseModel):
    name: str = Field(default='Unknown', min_length=2, max_length=30)
    last_name: str = Field(default='Unknown', min_length=2, max_length=40)
    email: EmailStr  # str =  Field(default='Unknown@mail.com', min_length=6, max_length=30, regex=...)  # i@i.ua
    phone: int = Field(default=1, gt=0, le=9999999999)
    birthday: date  # = Field(default=date.today())  # YYYY-MM-DD
    description: str = Field(default='-', max_length=3000)  # String


'''
class ContactQuery(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=30)
    last_name: str | None = Field(default=None, min_length=2, max_length=40)
    email: str | None = Field(default=None, min_length=6)  # i@i.ua
    phone: int | None = Field(default=None)  # Field(default=None, gt=0, le=9999999999)
    # birthday: date  # = Field(default=date.today())  # YYYY-MM-DD
    # description: str = Field(default='-', max_length=3000)  # String
'''


class ContactResponse(ContactModel):
    id: int = 1 

    class Config:
        orm_mode = True


class CatToNameModel(BaseModel):
    name: str = Field(default='Unknown-next', min_length=2, max_length=30)


class UserModel(BaseModel):
    """корисні дані запиту для створення нового користувача."""
    username: str = Field(min_length=2, max_length=30)
    email: str
    password: str = Field(min_length=6, max_length=10)


class UserDb(BaseModel):
    """визначає представлення бази даних користувача."""
    id: int
    username: str
    email: str
    created_at: datetime
    avatar: str

    class Config:
        """вказує, що модель UserDb використовується для представлення моделі ORM."""
        orm_mode = True


class UserResponse(BaseModel):
    """модель відповіді, яка містить у собі модель UserDb та поле відомостей detail з рядком."""
    user: UserDb
    detail: str = "User successfully created"


class TokenModel(BaseModel):
    """визначає відповідь при отриманні токенів доступу для користувача, що пройшов аутентифікацію."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
