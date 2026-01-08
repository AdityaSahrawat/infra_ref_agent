# app/services/logger.py
import logging
from logging import StreamHandler, Formatter
from typing import Optional

def configure_root_logger(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    if not root.handlers:
        handler = StreamHandler()
        fmt = Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
        handler.setFormatter(fmt)
        root.addHandler(handler)
    root.setLevel(level)

def get_logger(name: str):
    """
    Returns a standard logger. Call configure_root_logger() once at startup.
    """
    return logging.getLogger(name)
