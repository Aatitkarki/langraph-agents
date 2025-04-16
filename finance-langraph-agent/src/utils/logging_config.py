import logging
import sys
from colorlog import ColoredFormatter

def setup_logging(level=logging.DEBUG, package_name="src"):
    """Configures colored logging for the application with package-specific levels.

    Sets up a colored logging configuration that:
    - Uses colored output for different log levels
    - Shows time, level, logger name and message
    - Sets specific log level for the main package
    - Suppresses verbose logs from other libraries

    Args:
        level (int, optional): Logging level for the main package (default: DEBUG).
                               Use logging.DEBUG, logging.INFO, etc.
        package_name (str, optional): Root package name to apply logging level to
                                      (default: "src").

    Returns:
        None: This function configures logging globally.

    Configuration Details:
        - Log format: "%(asctime)s [%(levelname)s] [%(name)s] - %(message)s"
        - Colors: DEBUG=cyan, INFO=green, WARNING=yellow, ERROR=red, CRITICAL=bold_red
        - Time format: "%H:%M:%S" (hours:minutes:seconds)
        - Output: stdout
        - Other libraries: Set to CRITICAL level to reduce noise
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