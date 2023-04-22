from pydantic import BaseSettings


class Settings(BaseSettings):
    """Class for settings."""
    sqlalchemy_database_url: str
    secret_key: str
    algorithm: str
    mail_username: str
    mail_password: str
    mail_from: str  # = self.mail_username ?
    mail_port: int
    mail_server: str
    mail_from_name: str
    redis_host: str = 'localhost'
    redis_password: str
    redis_port: int = 6379
    limit_crit: int
    limit_warn: int
    cors_origins: str
    cors_credentials: str
    cors_methods: str
    cors_headers: str
    cloudinary_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str

    class Config:
        """Specifies the location of the .env environment file and its utf-8 encoding. This will allow you to read
        the contents of the .env file and assign its value to the corresponding variable. As you can see,
        case does not matter."""
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
