import logging
from rich.logging import RichHandler


logger = logging.getLogger(__name__)

# handlers
shell_handler = RichHandler()
file_handler = logging.FileHandler("debug.log")

# formatter
file_fmt = (
    f"%(levelname)s\t\t[%(asctime)s]                  "
    "\t\t%(filename)s:%(lineno)s\n%(funcName)s:\n%(message)s\n"
)
file_formatter = logging.Formatter(file_fmt, datefmt="%d-%m %H:%M")
file_handler.setFormatter(file_formatter)

logger.setLevel(logging.DEBUG)
shell_handler.setLevel(logging.DEBUG)
file_handler.setLevel(logging.DEBUG)

logger.addHandler(shell_handler)
logger.addHandler(file_handler)