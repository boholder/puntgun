def get_input(key: str) -> str:
    key_loop = True
    value = ''
    while key_loop:
        value = input('{}:'.format(key))
        # default yes
        confirm = input('confirm?([y]/n)')
        if not confirm or confirm.lower() == 'y':
            key_loop = False

    return value
