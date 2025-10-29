from colorama import Fore, Back, Style
import sys


def _print_with_color(color, msg: str, value):
    line = f"{color}{msg}"
    if value is not None:
        line += f":{Style.RESET_ALL} {value}"
    else:
        line += f"{Style.RESET_ALL}"
    sys.stdout.write(f"{line}\n")
    sys.stdout.flush()


def print_debug(msg: str, value=None):
    _print_with_color(Fore.WHITE, msg, value)


def print_temp(msg: str, value=None):
    _print_with_color(Fore.BLACK+Back.MAGENTA, msg, value)


def print_info(msg: str, value=None):
    _print_with_color(Fore.WHITE, msg, value)


def print_status(msg: str, value=None):
    _print_with_color(Fore.BLUE, msg, value)


def print_success(msg: str, value=None):
    _print_with_color(Fore.GREEN, msg, value)


def print_warning(msg: str, value=None):
    _print_with_color(Fore.YELLOW, msg, value)


def print_error(msg: str, value=None):
    _print_with_color(Fore.RED, msg, value)
