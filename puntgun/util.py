import logging
from typing import Dict, Any, List


def get_input_from_terminal(key: str) -> str:
    key_loop = True
    value = ''
    while key_loop:
        value = input('{}:'.format(key))
        # default yes
        confirm = input('confirm?([y]/n)')
        if not confirm or confirm.lower() == 'y':
            key_loop = False

    return value


# option the logging module
logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] %(message)s')


def get_logger(name: str) -> logging.Logger:
    """Let classes get their own logger with common configuration configured."""
    return logging.getLogger(name)


def log_error_with(cls_logger):
    """Decorator to log assertion failures.

    Let classes pass their own logger to this decorator,
    because get class definition via method is more complex.
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                cls_logger.error(e)
                raise e

        return wrapper

    return decorator


def get_instance_via_config(cls, config_pair: Dict[str, Any]):
    """
    Find same ``config_keyword`` in all given class's subclasses
    and return the instance of matched subclass.

    :param cls: indicated class
    :param config_pair: {config_keyword: value}
    :return: instance of one subclass of cls
    """
    keyword, value = config_pair.popitem()
    for subclass in cls.__subclasses__():
        if subclass.config_keyword == keyword:
            return subclass(value)
    raise ValueError(f"No such who field matches [{keyword}], "
                     f"please fix it in your configuration.")


def split_list(lst: list, n: int) -> List[list]:
    """Split list into n-size sub-lists."""
    return [lst[i:i + n] for i in range(0, len(lst), n)]
