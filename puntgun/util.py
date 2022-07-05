"""Util methods for many modules."""


def get_input_from_terminal(key: str) -> str:
    loop = True
    value = ''
    while loop:
        value = input('{}:'.format(key))
        # default yes
        confirm = input('confirm?([y]/n)')
        if not confirm or confirm.lower() == 'y':
            loop = False

    return value
