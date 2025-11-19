import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(log_path_str: str = "./logs/app.log", level: int = logging.DEBUG) -> None:
    handlers: list[logging.Handler] = []

    # console
    console = logging.StreamHandler()
    console.setLevel(level)
    handlers.append(console)

    # file
    log_path = Path(log_path_str)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    fileh = RotatingFileHandler(log_path, maxBytes=5_000_000, backupCount=3, encoding="utf-8")
    fileh.setLevel(level)
    handlers.append(fileh)

    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=level,
        format=fmt,
        datefmt=datefmt,
        handlers=handlers,
        force=True,          # force reloading of previous setting
    )

    # just in case.
    root = logging.getLogger()
    root.propagate = True
