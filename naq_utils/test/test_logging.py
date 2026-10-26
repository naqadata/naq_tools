from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from colorama import Fore, Back, Style
from naq_utils.logging import logger
import logging
import pytest


@pytest.fixture(autouse=True)
def init_logging(caplog):
    caplog.set_level(logging.DEBUG, logger = logger.name)


class TestConsole:

    @staticmethod
    def validate(caplog, level_name: str, substr: str, color: str, value: str):
        assert caplog.records
        record = caplog.records[-1]
        message = record.getMessage()
        return (
            record.levelname == level_name.upper()
            and substr in message
            and message.startswith(color)
            and message.endswith(value)
        )

    def test_logging_debug(self, caplog):
        logger.debug("Hello World", value="DEBUG value")
        assert self.validate(caplog, "DEBUG", "Hello World", Style.RESET_ALL, "DEBUG value")

    def test_logging_temp(self, caplog):
        logger.temp("Hello World", value="TEMP value")
        assert self.validate(caplog, "TEMP", "Hello World", Fore.BLACK+Back.MAGENTA, "TEMP value")

    def test_logging_info(self, caplog):
        logger.info("Hello World", value="INFO value")
        assert self.validate(caplog, "INFO", "Hello World", Style.RESET_ALL, "INFO value")

    def test_logging_status(self, caplog):
        logger.status("Hello World", value="STATUS value")
        assert self.validate(caplog, "STATUS", "Hello World", Fore.BLUE, "STATUS value")

    def test_logging_success(self, caplog):
        logger.success("Hello World", value="SUCCESS value")
        assert self.validate(caplog, "SUCCESS", "Hello World", Fore.GREEN, "SUCCESS value")

    def test_logging_warning(self, caplog):
        logger.warning("Hello World", value="WARNING value")
        assert self.validate(caplog, "WARNING", "Hello World", Fore.YELLOW, "WARNING value")

    def test_logging_error(self, caplog):
        logger.error("Hello World", value="ERROR value")
        assert self.validate(caplog, "ERROR", "Hello World", Fore.RED, "ERROR value")

    def test_logging_exception(self, caplog):
        logger.exception("Hello World", value="EXCEPTION value")
        assert self.validate(caplog, "ERROR", "Hello World", Fore.RED, "EXCEPTION value")

    def test_logging_critical(self, caplog):
        logger.critical("Hello World", value="CRITICAL value")
        assert self.validate(caplog, "CRITICAL", "Hello World", Fore.RED, "CRITICAL value")
