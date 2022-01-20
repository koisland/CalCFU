import logging
from .calc_config import CalcConfig

# Create the logger and set level to info.
loggers = logging.getLogger(__name__)
loggers.setLevel(logging.INFO)

# Create the Handler for logging data to a file
logger_handler = logging.FileHandler(filename=CalcConfig.FPATH_LOG, mode="a")
logger_handler.setLevel(logging.INFO)

# Create a Formatter for formatting the log messages (time - module - level - msg)
logger_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add the Formatter to the Handler
logger_handler.setFormatter(logger_formatter)

loggers.addHandler(logger_handler)

