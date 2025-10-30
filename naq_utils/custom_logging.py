import logging
import sys
from colorama import Back, Fore, Style

STATUS = logging.INFO + 5
logging.addLevelName(STATUS, "STATUS")

class NaqLogger(logging.Logger):
    def __init__(self, name, level = logging.DEBUG):
        super().__init__(name, level)
        self.propagate = False

        console_formatter = logging.Formatter("[%(asctime)s] %(levelname)10s => %(message)s")

        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(console_formatter)
        handler.setLevel(logging.DEBUG)

        self.addHandler(handler)

    def _log(self, level, msg, colors=Style.RESET_ALL, *args, **kwargs):        
        if self.isEnabledFor(level):
            msg = f"{colors}{msg}{Style.RESET_ALL}"
            if 'value' in kwargs:
                msg = f"{msg}: {kwargs.pop('value')}"
            if 'prefix' in kwargs:
                msg = f"{Style.RESET_ALL}[{kwargs.pop('prefix')}] {msg}"
            super()._log(level, msg, args, **kwargs)

    def temp(self, msg, *args, **kwargs):
        self._log(STATUS, msg, colors=Fore.BLACK+Back.MAGENTA, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        self._log(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._log(logging.INFO, msg, *args, **kwargs)

    def status(self, msg, *args, **kwargs):
        self._log(STATUS, msg, colors=Fore.BLUE, *args, **kwargs)

    def success(self, msg, *args, **kwargs):
        self._log(STATUS, msg, colors=Fore.GREEN, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._log(logging.WARNING, msg, colors=Fore.YELLOW, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._log(logging.ERROR, msg, colors=Fore.RED, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        kwargs["exc_info"] = True
        self._log(logging.ERROR, msg, colors=Fore.RED, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self._log(logging.CRITICAL, msg, colors=Fore.RED, *args, **kwargs)


logging.setLoggerClass(NaqLogger)

logger: NaqLogger = logging.getLogger("NAQ") # type: ignore
