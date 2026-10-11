"""Gunicorn logger that writes error and access logs as JSON lines.

Enabled via ``logger_class`` in ``gunicorn.conf``. Kept apart from
``pydotorg.logs`` because gunicorn is only installed with the ``prod`` extra.
"""

from gunicorn import glogging

from pydotorg.logs import json_formatter


class JSONLogger(glogging.Logger):
    """Gunicorn logger rendering through ``pydotorg.logs.json_formatter``."""

    def setup(self, cfg):
        """Configure gunicorn's handlers, then swap their formatters for JSON."""
        super().setup(cfg)
        formatter = json_formatter()
        for log in (self.error_log, self.access_log):
            for handler in log.handlers:
                if getattr(handler, "_gunicorn", False):
                    handler.setFormatter(formatter)

    def access(self, resp, req, environ, request_time):
        """Log one request with method, path, status, and duration as fields."""
        if not self.access_log_enabled:
            return
        try:
            status = resp.status
            if isinstance(status, str):
                status = status.split(None, 1)[0]
            method = environ["REQUEST_METHOD"]
            # gunicorn's error path passes a minimal environ: no PATH_INFO, QUERY_STRING, or HTTP_*.
            fields = {
                "method": method,
                "path": environ.get("PATH_INFO", getattr(req, "path", "")),
                "query": environ.get("QUERY_STRING", getattr(req, "query", "")),
                "status": int(status),
                "bytes": getattr(resp, "sent", None),
                "duration_ms": round(request_time.total_seconds() * 1000, 3),
                "protocol": environ.get("SERVER_PROTOCOL"),
                "referer": environ.get("HTTP_REFERER", ""),
                "user_agent": environ.get("HTTP_USER_AGENT", ""),
                # Set by nginx; django-structlog binds the same value to app log lines.
                "request_id": environ.get("HTTP_X_REQUEST_ID")
                or next((value for name, value in getattr(req, "headers", ()) if name == "X-REQUEST-ID"), ""),
            }
            self.access_log.info("%s %s", method, environ["RAW_URI"], extra=fields)
        except Exception:  # noqa: BLE001 - mirror gunicorn: never let logging break a response
            self.exception("Failed to write access log")
