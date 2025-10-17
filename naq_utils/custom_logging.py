import logging
from logging import *
from colorama import Back, Fore, Style

STATUS = INFO + 5
addLevelName(STATUS, "STATUS")


console_formatter = Formatter(
    "[%(asctime)s] %(levelname)10s => %(message)s")


def init(log_level=STATUS):
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.propagate = False

    handler = logging.StreamHandler()
    handler.setFormatter(console_formatter)
    handler.setLevel(log_level)

    logger.handlers = []
    logger.addHandler(handler)


# noinspection PyProtectedMember
def _log(level, logger_name, msg, colors=Style.RESET_ALL,  *args, **kwargs):
    logger = getLogger(name=logger_name)
    if logger.isEnabledFor(level):
        msg = f"{colors}{msg}{Style.RESET_ALL}"
        if 'value' in kwargs:
            msg = f"{msg}: {kwargs.pop('value')}"
        if 'prefix' in kwargs:
            msg = f"{Style.RESET_ALL}[{kwargs.pop('prefix')}] {msg}"
        logger._log(level, msg, args, **kwargs)


def temp(msg, *args, logger_name=None, **kwargs):
    _log(STATUS, logger_name, msg, colors=Fore.BLACK+Back.MAGENTA, *args, **kwargs)


def debug(msg, *args, logger_name=None, **kwargs):
    _log(DEBUG, logger_name, msg, *args, **kwargs)


def info(msg, *args, logger_name=None, **kwargs):
    _log(INFO, logger_name, msg, *args, **kwargs)


def status(msg, *args, logger_name=None, **kwargs):
    _log(STATUS, logger_name, msg, colors=Fore.BLUE, *args, **kwargs)


def success(msg, *args, logger_name=None, **kwargs):
    _log(STATUS, logger_name, msg, colors=Fore.GREEN, *args, **kwargs)


def warning(msg, *args, logger_name=None, **kwargs):
    _log(WARNING, logger_name, msg, colors=Fore.YELLOW, *args, **kwargs)


def error(msg, *args, logger_name=None, **kwargs):
    _log(ERROR, logger_name, msg, colors=Fore.RED, *args, **kwargs)


def exception(msg, *args, logger_name=None, **kwargs):
    kwargs["exc_info"] = True
    _log(ERROR, logger_name, msg, colors=Fore.RED, *args, **kwargs)


def critical(msg, *args, logger_name=None, **kwargs):
    _log(CRITICAL, logger_name, msg, colors=Fore.RED, *args, **kwargs)
