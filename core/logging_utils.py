#core/logging_utils.py
import logging
import os

_CONFIGURED = False


def get_logger(name: str) -> logging.Logger:
    global _CONFIGURED
    if not _CONFIGURED:
        level_name = os.getenv("LOG_LEVEL", "INFO").upper()
        level = getattr(logging, level_name, logging.INFO)
        fmt = os.getenv(
            "LOG_FORMAT",
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        )
        logging.basicConfig(level=level, format=fmt)
        _CONFIGURED = True
    return logging.getLogger(name)
