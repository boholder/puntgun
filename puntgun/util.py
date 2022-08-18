"""Util methods for many modules."""
import os
import shutil
from pathlib import Path

from loguru import logger


def get_input_from_terminal(key: str) -> str:
    """A more friendly mistake-tolerating input method"""
    loop = True
    value = ''
    while loop:
        value = input('{}:'.format(key))
        confirm = input('confirm?([y]/n)')
        # default yes
        if not confirm or confirm.lower() == 'y':
            loop = False

    return value


def backup_if_exists(path: Path):
    if path.exists():
        logger.warning("Indicated output file [{}] already exists, back up the origin file", path)
        shutil.copy2(path, path.with_suffix(os.path.splitext(path)[1] + '.bak'))
