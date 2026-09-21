from flask import Blueprint
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from app.logging_config import event

bp = Blueprint("health", __name__)


@bp.get("/health")
def health():
    return {"status": "healthy", "service": "shop-app"}


@bp.get("/ready")
def ready():
    try:
        db.session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        db.session.rollback()
        event("DB_CONNECTION_FAILED", 503)
        return {"status": "not_ready", "database": "disconnected"}, 503
    return {"status": "ready", "database": "connected"}
