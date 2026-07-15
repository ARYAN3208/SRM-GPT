import logging
import os
import time
import json
from pathlib import Path
from logging.handlers import RotatingFileHandler
import contextvars
from contextlib import contextmanager

_request_id = contextvars.ContextVar("request_id", default="-")

def set_request_id(rid: str):
    _request_id.set(rid)

def get_request_id() -> str:
    return _request_id.get()

class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id.get()
        return True

class JsonOnlyFilter(logging.Filter):
    """Allow only JSON messages into the jsonl handler."""
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        return isinstance(msg, str) and msg.startswith("{") and msg.endswith("}")

def _level() -> str:
    return os.getenv("LOG_LEVEL", "INFO").upper()

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.propagate = False

    if logger.handlers:
        return logger

    level = _level()
    logger.setLevel(level)

    log_dir = Path("app/data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    text_log = log_dir / "rag_app.log"
    json_log = log_dir / "rag_app.jsonl"
    info_log = log_dir / "info_log.txt"
    error_log = log_dir / "error_log.txt"

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | rid=%(request_id)s | %(message)s"
    )

    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(fmt)
    ch.addFilter(RequestIdFilter())

    fh = RotatingFileHandler(text_log, maxBytes=5_000_000, backupCount=5, encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(fmt)
    fh.addFilter(RequestIdFilter())

    jh = RotatingFileHandler(json_log, maxBytes=5_000_000, backupCount=5, encoding="utf-8")
    jh.setLevel(level)
    jh.setFormatter(logging.Formatter("%(message)s"))
    jh.addFilter(RequestIdFilter())
    jh.addFilter(JsonOnlyFilter())

    # Dedicated info log: captures INFO level and above
    ih = RotatingFileHandler(info_log, maxBytes=5_000_000, backupCount=5, encoding="utf-8")
    ih.setLevel(logging.INFO)
    ih.setFormatter(fmt)
    ih.addFilter(RequestIdFilter())

    # Dedicated error log: captures only ERROR level and above
    eh = RotatingFileHandler(error_log, maxBytes=5_000_000, backupCount=5, encoding="utf-8")
    eh.setLevel(logging.ERROR)
    eh.setFormatter(fmt)
    eh.addFilter(RequestIdFilter())

    logger.addHandler(ch)
    logger.addHandler(fh)
    logger.addHandler(jh)
    logger.addHandler(ih)
    logger.addHandler(eh)

    return logger

def log_json(logger: logging.Logger, event: str, **fields):
    payload = {
        "ts": time.time(),
        "event": event,
        "rid": get_request_id(),
        **fields,
    }
    logger.info(json.dumps(payload, ensure_ascii=False))

@contextmanager
def span(logger: logging.Logger, name: str, **fields):
    t0 = time.perf_counter()
    log_json(logger, f"{name}.start", **fields)
    try:
        yield
        log_json(logger, f"{name}.end", elapsed_ms=round((time.perf_counter() - t0) * 1000, 2))
    except Exception as e:
        log_json(logger, f"{name}.error", elapsed_ms=round((time.perf_counter() - t0) * 1000, 2), error=str(e))
        logger.exception(f"{name} failed")
        raise