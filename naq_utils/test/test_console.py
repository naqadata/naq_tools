from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from naq_utils import console
from colorama import Fore, Back


class OutputCapture:
    def __init__(self):
        self.stdout = None
        self.stderr = None

        self._stdout_buffer = StringIO()
        self._stderr_buffer = StringIO()

        self._stdout_redirector = redirect_stdout(self._stdout_buffer)
        self._stderr_redirector = redirect_stderr(self._stderr_buffer)

    def __enter__(self):
        self._stdout_redirector.__enter__()
        self._stderr_redirector.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stdout_redirector.__exit__(exc_type, exc_val, exc_tb)
        self._stderr_redirector.__exit__(exc_type, exc_val, exc_tb)

        self.stdout = self._stdout_buffer.getvalue()
        self.stderr = self._stderr_buffer.getvalue()


class TestConsole:

    @staticmethod
    def _assert_format(text: str, substr: str, color: str, value: str):
        assert substr in text
        assert text.startswith(color)
        assert text.endswith(f"{value}\n")

    def test_print_debug(self):
        with OutputCapture() as capture:
            console.print_debug("Hello World", value="DEBUG value")

        self._assert_format(capture.stdout, "Hello World", Fore.WHITE, "DEBUG value")

    def test_print_temp(self):
        with OutputCapture() as capture:
            console.print_temp("Hello World", value="TEMP value")

        self._assert_format(capture.stdout, "Hello World", Fore.BLACK+Back.MAGENTA, "TEMP value")

    def test_print_info(self):
        with OutputCapture() as capture:
            console.print_info("Hello World", value="INFO value")

        self._assert_format(capture.stdout, "Hello World", Fore.WHITE, "INFO value")

    def test_print_status(self):
        with OutputCapture() as capture:
            console.print_status("Hello World", value="STATUS value")

        self._assert_format(capture.stdout, "Hello World", Fore.BLUE, "STATUS value")

    def test_print_success(self):
        with OutputCapture() as capture:
            console.print_success("Hello World", value="SUCCESS value")

        self._assert_format(capture.stdout, "Hello World", Fore.GREEN, "SUCCESS value")

    def test_print_warning(self):
        with OutputCapture() as capture:
            console.print_warning("Hello World", value="WARNING value")

        self._assert_format(capture.stdout, "Hello World", Fore.YELLOW, "WARNING value")

    def test_print_error(self):
        with OutputCapture() as capture:
            console.print_error("Hello World", value="ERROR value")

        self._assert_format(capture.stdout, "Hello World", Fore.RED, "ERROR value")