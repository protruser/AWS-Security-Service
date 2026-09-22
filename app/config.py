import os
from sqlalchemy import URL


class Config:
    # vuln_service only: opt in explicitly in the local Compose environment.
    VULNERABLE_LAB = False
    TRUST_PROXY_HEADERS = False

    BRUTE_FORCE_THRESHOLD = 5
    BRUTE_FORCE_WINDOW_SECONDS = 300

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    MAX_CONTENT_LENGTH = 16 * 1024


class DevelopmentConfig(Config):
    SESSION_COOKIE_SECURE = False


class LabConfig(Config):
    VULNERABLE_LAB = True
    SESSION_COOKIE_SECURE = True
    TRUST_PROXY_HEADERS = True


class ProductionConfig(Config):
    SESSION_COOKIE_SECURE = True
    TRUST_PROXY_HEADERS = True


def environment_config():
    env = os.getenv("FLASK_ENV", "development").strip().lower()
    vulnerable = os.getenv("VULNERABLE_LAB", "0") == "1"
    
    configs = {
        "development": DevelopmentConfig,
        "lab": LabConfig,
        "production": ProductionConfig,
    }

    if env not in configs:
        raise ValueError(
            "FLASK_ENV must be development, lab, or production"
        )

    if vulnerable and env not in {"development", "lab"}:
        raise ValueError(
            "VULNERABLE_LAB is allowed only in development or lab"
        )

    if env == "lab" and not vulnerable:
        raise ValueError(
            "FLASK_ENV=lab requires VULNERABLE_LAB=1"
        )

    secret = os.environ.get("SECRET_KEY")
    if not secret or len(secret) < 32:
        raise ValueError(
            "SECRET_KEY must contain at least 32 characters"
        )

    return configs[env], {
        "SECRET_KEY": secret,
        "VULNERABLE_LAB": vulnerable,
        "SQLALCHEMY_DATABASE_URI": URL.create(
            "mysql+pymysql",
            username=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            host=os.getenv("DB_HOST", "shop-db"),
            port=int(os.getenv("DB_PORT", "3306")),
            database=os.environ["DB_NAME"],
            query={"charset": "utf8mb4"},
        ),
    }
