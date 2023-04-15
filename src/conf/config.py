from pydantic import BaseSettings


class Settings(BaseSettings):
    sqlalchemy_database_url: str
    secret_key: str
    algorithm: str
    mail_username: str
    mail_password: str
    mail_from: str  # = self.mail_username
    mail_port: int
    mail_server: str
    mail_from_name: str
    redis_host: str = 'localhost'
    redis_password: str
    redis_port: int = 6379

    class Config:
        """Задає розташування файлу середовища .env та його кодування utf-8. 
        Це дасть змогу прочитати вміст файлу .env і присвоїти відповідній змінній 
        своє значення. Як бачимо, регістр значення не має.
        """
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
