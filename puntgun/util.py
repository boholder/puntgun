import logging


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


# config the logging module
logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] %(message)s')


def get_logger(name: str) -> logging.Logger:
    """Let classes get their own logger with common configuration"""
    return logging.getLogger(name)


def log_assertion_error_with(cls_logger):
    """Decorator to log assertion failures.

    Let classes pass their own logger to this decorator,
    because get class definition via method is more complex.
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except AssertionError as e:
                cls_logger.error(e)
                raise e

        return wrapper

    return decorator
