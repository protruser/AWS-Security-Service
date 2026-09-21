import json
import logging
import sys
import uuid
from datetime import datetime, timezone
from flask import g, has_request_context, request


SCENARIOS = {
    "LOGIN_SUCCESS": "BRUTE_FORCE", "LOGIN_FAILED": "BRUTE_FORCE",
    "BRUTE_FORCE_SUSPECTED": "BRUTE_FORCE",
    "SUSPICIOUS_PATH_REQUEST": "DIRECTORY_SEARCH", "INVALID_PATH": "DIRECTORY_SEARCH",
    "SUSPICIOUS_SEARCH_INPUT": "SQL_INJECTION", "DATABASE_QUERY_ERROR": "SQL_INJECTION",
    "PRODUCT_SEARCH": "SQL_INJECTION", "SUSPICIOUS_REVIEW_INPUT": "XSS", "REVIEW_CREATED": "XSS",
}


def request_scenario(name):
    if name in SCENARIOS:
        return SCENARIOS[name]
    if has_request_context():
        endpoint = request.endpoint or ""
        if endpoint == "auth.login":
            return "BRUTE_FORCE"
        if endpoint.startswith("reviews."):
            return "XSS"
        if endpoint == "products.search":
            return "SQL_INJECTION"
    return None


class JsonFormatter(logging.Formatter):
    def format(self, record):
        active = has_request_context()
        return json.dumps({
            "event_id": getattr(record, "event_id", None) or str(uuid.uuid4()),
            "scenario_id": getattr(record, "scenario_id", None),
            "severity": getattr(record, "severity", "HIGH"),
            "source": "SHOP_APP",
            "action": getattr(record, "action", "DETECTED"),
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "event_type": getattr(record, "event_type", "SERVER_ERROR"),
            "source_ip": request.remote_addr if active else None,
            "target": "shop-flask",
            "path": request.path if active else None,
            "method": request.method if active else None,
            "status_code": getattr(record, "status_code", 500),
            "request_id": getattr(g, "request_id", None) if active else None,
        }, ensure_ascii=True)


def configure_logging(app):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    app.logger.handlers = [handler]
    app.logger.propagate = False
    app.logger.setLevel(logging.INFO)


def event(name, status=200):
    from flask import current_app
    detected = name.startswith("SUSPICIOUS_") or name in {
        "LOGIN_FAILED", "BRUTE_FORCE_SUSPECTED", "INVALID_PATH", "INPUT_VALIDATION_FAILED",
    } or status >= 400
    current_app.logger.log(logging.ERROR if status >= 500 else logging.INFO,
                           name, extra={"event_type": name, "status_code": status,
                                        "event_id": str(uuid.uuid4()), "scenario_id": request_scenario(name),
                                        "severity": "HIGH" if detected else "INFO",
                                        "action": "DETECTED" if detected else "NORMAL"})
