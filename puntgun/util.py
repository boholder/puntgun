"""Util methods for many modules."""


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
