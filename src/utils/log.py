import logging

def get_logger(name: str = "static_engine") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    h = logging.StreamHandler()
    fmt = logging.Formatter("[%(levelname)s] %(message)s")
    h.setFormatter(fmt)
    logger.addHandler(h)
    return logger