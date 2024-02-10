import os


class Config(object):
    """Base configuration."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "your_secret_key")
    DATABASE_URI = os.environ.get("DATABASE_URI", "sqlite:///yourdatabase.db")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "your_openai_api_key")


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
