import os


class Config(object):
    """Base configuration."""

    DATABASE_URI = os.environ.get(
        "DATABASE_URI", "sqlite:///data/processed/embeddings.db"
    )
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "your_openai_api_key")
    FAISS_INDEX_PATH = os.environ.get(
        "FAISS_INDEX_PATH", "data/processed/faiss_index.index"
    )

    CORS_ALLOWED_ORIGINS = [
        "https://huberman-gpt-gamma.vercel.app",
        "https://localhost:3000",
        "http://localhost:3000",
        "http://localhost:5000",
        "http://localhost:8080",
    ]


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
