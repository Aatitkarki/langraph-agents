import logging
import sys

def setup_logging(level=logging.INFO):
    """
    Configures the root logger for the application.

    Args:
        level: The minimum logging level to output (e.g., logging.INFO, logging.DEBUG).
    """
    log_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(name)s] - %(message)s"
    )
    
    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates if called multiple times
    # (though it should ideally be called only once)
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Add a console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    # Optional: Add a file handler
    # file_handler = logging.FileHandler("app.log")
    # file_handler.setFormatter(log_formatter)
    # root_logger.addHandler(file_handler)

    logging.info("Logging configured successfully.")