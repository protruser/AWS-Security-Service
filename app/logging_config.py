import json
import logging
import sys
from datetime import datetime, timezone
from flask import g, has_request_context, request


class JsonFormatter(logging.Formatter):
    def format(self, record):
        active = has_request_context()
        return json.dumps({
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
    current_app.logger.log(logging.ERROR if status >= 500 else logging.INFO,
                           name, extra={"event_type": name, "status_code": status})
