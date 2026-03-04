from __future__ import annotations

import logging
from pathlib import Path


class QueueLogger:
    def __init__(self, emit):
        self.emit = emit

    def info(self, msg: str):
        self.emit(msg, "info")

    def ok(self, msg: str):
        self.emit(msg, "ok")

    def warn(self, msg: str):
        self.emit(msg, "warn")

    def error(self, msg: str):
        self.emit(msg, "err")

    def head(self, msg: str):
        self.emit(msg, "head")


def file_logger(log_file: Path) -> logging.Logger:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("uoffer_portable")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)
    return logger
