import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from careermail.core import paths

_configured = False


def setup_logging(level: str = "INFO", retention_days: int = 30) -> Path:
    global _configured
    log_dir = paths.log_dir()
    if _configured:
        return log_dir

    level_num = getattr(logging, level.upper(), logging.INFO)
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(level_num)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level_num)
    ch.setFormatter(fmt)
    root.addHandler(ch)

    # Main rotating log
    app_log = log_dir / "careermail.log"
    fh = TimedRotatingFileHandler(
        app_log, when="midnight", interval=1, backupCount=retention_days, encoding="utf-8"
    )
    fh.setLevel(level_num)
    fh.setFormatter(fmt)
    root.addHandler(fh)

    # Error only log
    err_log = log_dir / "error.log"
    efh = TimedRotatingFileHandler(
        err_log, when="midnight", interval=1, backupCount=retention_days, encoding="utf-8"
    )
    efh.setLevel(logging.ERROR)
    efh.setFormatter(fmt)
    root.addHandler(efh)

    _configured = True
    return log_dir
