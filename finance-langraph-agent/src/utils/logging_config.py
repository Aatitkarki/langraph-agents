import logging
import sys
from colorlog import ColoredFormatter

def setup_logging(level=logging.DEBUG, package_name="src"):
    """
    Configures logging:
    - Your package logs at `level` (e.g. DEBUG)
    - Other libraries log at INFO or above
    """
    log_format = "%(log_color)s%(asctime)s [%(levelname)s] [%(name)s] - %(message)s"
    log_colors = {
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    }

    # Only the time, no date
    datefmt = "%H:%M:%S"  # Format for hours:minutes:seconds

    formatter = ColoredFormatter(
        log_format, datefmt=datefmt, reset=True, log_colors=log_colors
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all, we'll filter below

    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Set your package's logger to DEBUG (or whatever level you pass in)
    logging.getLogger(package_name).setLevel(level)

    # Set all other loggers (propagated to root) to INFO
    for name in logging.root.manager.loggerDict:
        if not name.startswith(package_name):
            logging.getLogger(name).setLevel(logging.CRITICAL)

    logging.getLogger(package_name).info("Logging configured.")