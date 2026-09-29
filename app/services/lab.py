"""Intentional vulnerabilities for vuln_service, authorized local dummy data only.

Detection is illustrative, not a security filter. Replace vulnerable_search with
ORM binding and the review partial with autoescaping when implementing fixes.
"""
import re
from datetime import timedelta

from flask import current_app, g, request
from sqlalchemy import func, text

from app.extensions import db
from app.logging_config import event
from app.models import LoginAttempt, Product, utcnow


SUSPICIOUS_PATHS = frozenset({"/admin", "/backup", "/old", "/config"})
SEARCH_PATTERN = re.compile(r"['\";#]|--|/\*|\b(union|select|sleep|benchmark)\b", re.I)
REVIEW_PATTERN = re.compile(r"<[^>]+>|\bon\w+\s*=|javascript\s*:", re.I)


def suspicious_search(value):
    return bool(SEARCH_PATTERN.search(value))


def suspicious_review(value):
    return bool(REVIEW_PATTERN.search(value))


def vulnerable_search(query):
    # vuln_service ONLY: quotes intentionally unbound; no extra DB privileges.
    # Keep literal wildcard search semantics. This is NOT SQL sanitization.
    pattern = query.replace("!", "!!").replace("%", "!%").replace("_", "!_")
    sql = "SELECT * FROM products WHERE name LIKE '%" + pattern + "%' ESCAPE '!' ORDER BY id"
    return db.session.scalars(db.select(Product).from_statement(text(sql))).all()


def review_partial():
    return "lab/review_content.html" if current_app.config["VULNERABLE_LAB"] else "review_content.html"


def record_login_attempt(username, success, status):
    # No passwords, cookies or tokens accepted by this API. Preserve the schema.
    username = username.strip()[:80]
    source_ip = request.remote_addr or "unknown"
    db.session.add(LoginAttempt(username=username, source_ip=source_ip, success=success))
    db.session.commit()
    g.login_attempt_recorded = True
    event("LOGIN_SUCCESS" if success else "LOGIN_FAILED", status)
    if success:
        return
    cutoff = utcnow() - timedelta(seconds=current_app.config["BRUTE_FORCE_WINDOW_SECONDS"])
    base = db.select(func.count()).select_from(LoginAttempt).where(
        LoginAttempt.success.is_(False), LoginAttempt.created_at >= cutoff)
    # Count IP and account separately: do not combine unrelated failures.
    ip_count = db.session.scalar(base.where(LoginAttempt.source_ip == source_ip))
    account_count = db.session.scalar(base.where(LoginAttempt.username == username)) if username else 0
    if max(ip_count, account_count) >= current_app.config["BRUTE_FORCE_THRESHOLD"]:
        # vuln_service: detection never locks, throttles or blocks a request.
        event("BRUTE_FORCE_SUSPECTED", status)
