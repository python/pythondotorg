"""structlog setup shared by Django, Celery, and gunicorn.

Both structlog loggers and stdlib ``logging`` records (Django, Celery, gunicorn,
third-party libraries) render through ``structlog.stdlib.ProcessorFormatter``:
``json_formatter`` for production (one JSON object per line) and
``console_formatter`` for local development.
"""

import structlog

# Applied to every entry. Context bound by django-structlog's RequestMiddleware
# (request_id, user_id) is merged into stdlib records too.
_SHARED_PROCESSORS = [
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    structlog.processors.TimeStamper(fmt="iso", utc=True),
    structlog.processors.StackInfoRenderer(),
]

# Stdlib records also carry fields passed via ``extra=``.
_FOREIGN_PRE_CHAIN = [*_SHARED_PROCESSORS, structlog.stdlib.ExtraAdder()]


def configure_structlog():
    """Route structlog loggers through stdlib ``logging`` so ``LOGGING`` picks the renderer."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            *_SHARED_PROCESSORS,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def json_formatter():
    """Return a formatter that writes each entry as one JSON object."""
    return structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=_FOREIGN_PRE_CHAIN,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
    )


def console_formatter():
    """Return a formatter that writes aligned, human-readable lines."""
    return structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=_FOREIGN_PRE_CHAIN,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.dev.ConsoleRenderer(),
        ],
    )
