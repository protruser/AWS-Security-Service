import os
from sqlalchemy import URL


class Config:
    # vuln_service only: opt in explicitly in the local Compose environment.
    VULNERABLE_LAB = False
    BRUTE_FORCE_THRESHOLD = 5
    BRUTE_FORCE_WINDOW_SECONDS = 300
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    MAX_CONTENT_LENGTH = 16 * 1024


class DevelopmentConfig(Config):
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    SESSION_COOKIE_SECURE = True


def environment_config():
    env = os.getenv("FLASK_ENV", "development")
    vulnerable = os.getenv("VULNERABLE_LAB", "0") == "1"
    if vulnerable and env != "development":
        raise ValueError("VULNERABLE_LAB requires the local development environment")
    if env not in {"development", "production"}:
        raise ValueError("FLASK_ENV must be development or production")
    secret = os.environ.get("SECRET_KEY")
    if not secret or len(secret) < 32:
        raise ValueError("SECRET_KEY must contain at least 32 characters")
    return (ProductionConfig if env == "production" else DevelopmentConfig), {
        "SECRET_KEY": secret,
        "VULNERABLE_LAB": vulnerable,
        "SQLALCHEMY_DATABASE_URI": URL.create(
            "mysql+pymysql", username=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"], host=os.getenv("DB_HOST", "shop-db"),
            port=int(os.getenv("DB_PORT", "3306")), database=os.environ["DB_NAME"],
            query={"charset": "utf8mb4"},
        ),
    }
