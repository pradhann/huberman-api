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


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
