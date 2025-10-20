import logging
from functools import wraps

logger = logging.getLogger(__name__)

def log_exceptions(msg="Unhandled Error"):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception:
                logging.getLogger(fn.__module__).exception("%s in %s", msg, fn.__name__)
                raise
        return wrapper
    return deco