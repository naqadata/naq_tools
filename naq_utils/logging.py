import logging
import sys
from colorama import Back, Fore, Style

STATUS = logging.INFO + 5
SUCCESS = STATUS + 1
TEMP = logging.WARNING + 1

logging.addLevelName(STATUS, "STATUS")
logging.addLevelName(SUCCESS, "SUCCESS")
logging.addLevelName(TEMP, "TEMP")

class NaqLogger(logging.Logger):
    def __init__(self, name, level = logging.DEBUG):
        super().__init__(name, level)
        self.propagate = False

        console_formatter = logging.Formatter("[%(asctime)s] %(levelname)10s => %(message)s")

        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(console_formatter)
        handler.setLevel(level)

        self.addHandler(handler)

    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False, stacklevel=1, colors=Style.RESET_ALL, value=None, prefix=None, **kwargs):
        if self.isEnabledFor(level):
            msg = f"{colors}{msg}{Style.RESET_ALL}"
            if value:
                msg = f"{msg}: {value}"
            if prefix:
                msg = f"{Style.RESET_ALL}[{prefix}] {msg}"
            super()._log(level, msg, args, **kwargs)

    def temp(self, msg, *args, value=None, prefix=None, **kwargs):
        self._log(TEMP, msg, args, colors=Fore.BLACK+Back.MAGENTA, value=value, prefix=prefix, **kwargs)

    def debug(self, msg, *args, value=None, prefix=None, **kwargs):
        self._log(logging.DEBUG, msg, args, value=value, prefix=prefix, **kwargs)

    def info(self, msg, *args, value=None, prefix=None, **kwargs):
        self._log(logging.INFO, msg, args, value=value, prefix=prefix, **kwargs)

    def status(self, msg, *args, value=None, prefix=None, **kwargs):
        self._log(STATUS, msg, args, colors=Fore.BLUE, value=value, prefix=prefix, **kwargs)

    def success(self, msg, *args, value=None, prefix=None, **kwargs):
        self._log(SUCCESS, msg, args, colors=Fore.GREEN, value=value, prefix=prefix, **kwargs)

    def warning(self, msg, *args, value=None, prefix=None, **kwargs):
        self._log(logging.WARNING, msg, args, colors=Fore.YELLOW, value=value, prefix=prefix, **kwargs)

    def error(self, msg, *args, value=None, prefix=None, **kwargs):
        self._log(logging.ERROR, msg, args, colors=Fore.RED, value=value, prefix=prefix, **kwargs)

    def exception(self, msg, *args, value=None, prefix=None, **kwargs):
        kwargs["exc_info"] = True
        self._log(logging.ERROR, msg, args, colors=Fore.RED, value=value, prefix=prefix, **kwargs)

    def critical(self, msg, *args, value=None, prefix=None, **kwargs):
        self._log(logging.CRITICAL, msg, args, colors=Fore.RED, value=value, prefix=prefix, **kwargs)


logging.setLoggerClass(NaqLogger)

logger: NaqLogger = logging.getLogger("NAQ") # type: ignore
