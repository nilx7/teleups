import os
import logging
from typing import Optional


def setup_logger():
    log_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "ups_monitor.log"
    )
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )
    logger = logging.getLogger(__name__)
    return logger


def handle_logging(level: int, message: str, logger: Optional[logging.Logger] = None) -> None:
    """
    Handles logging or printing messages based on the availability of a logger.

    Args:
        level (int): The log level for the message.
        message (str): The message to log or print.
    """
    if logger:
        logger.log(level, message)
    else:
        print(message)
