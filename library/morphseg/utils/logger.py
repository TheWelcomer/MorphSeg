import logging
from rich.logging import RichHandler

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
shell_handler = RichHandler()
shell_handler.setLevel(logging.DEBUG)
logger.addHandler(shell_handler)
