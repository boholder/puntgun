"""Util methods for many modules."""
import getpass
import os
import shutil
from pathlib import Path
from typing import Callable

from loguru import logger


def get_input_from_terminal(key: str) -> str:
    return get_input_wrapper(input, '{}: '.format(key))


def get_secret_from_terminal(key: str) -> str:
    return get_input_wrapper(getpass.getpass, prompt='{}: '.format(key))


def get_input_wrapper(func: Callable, *args, **kwargs):
    """A more friendly mistake-tolerating input method"""
    loop = True
    value = ''
    while loop:
        value = func(*args, **kwargs)
        confirm = input('confirm?([y]/n)')
        # default yes
        if not confirm or confirm.lower() == 'y':
            loop = False

    return value


def backup_if_exists(path: Path):
    if path.exists():
        logger.warning("Indicated output file [{}] already exists, back up the origin file", path)
        shutil.copy2(path, path.with_suffix(os.path.splitext(path)[1] + '.bak'))
