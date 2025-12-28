import logging
from logging.config import dictConfig
from app.core.config import settings

def configure_logging() -> None:
    _level = getattr(settings, "LOG_LEVEL", "INFO")
    if isinstance(_level, str):
        _level = _level.upper()
    if _level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        _level = "INFO"

    formatters: dict = {
        "default": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        }
    }
    try:
        from pythonjsonlogger import jsonlogger  # type: ignore
    except Exception:
        pass
    else:
        formatters["json"] = {
            "()": jsonlogger.JsonFormatter,
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        }

    dictConfig({
         "version": 1,
         "disable_existing_loggers": False,
         "formatters": formatters,
         "handlers": {
             "console": {
                 "class": "logging.StreamHandler",
                 "formatter": "default",
                 "level": _level,
             },
         },
         "root": {
             "handlers": ["console"],
             "level": _level,
         },
         "loggers": {
             "uvicorn.error": {"level": _level, "propagate": True},
             "uvicorn.access": {"level": "INFO", "propagate": False},
         },
     })