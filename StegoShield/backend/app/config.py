import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    SECRET_KEY = os.getenv('SECRET_KEY', 'stegosheild-dev-key-2025')

    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')

    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 100 * 1024 * 1024))

    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp'}

    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')

    @staticmethod
    def init_app():
        """Ensure upload directory exists."""
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
