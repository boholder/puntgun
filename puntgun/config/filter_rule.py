class FilterRule:
    """
    Model, a mapping of same name configuration option.
    """

    def __init__(self, check_func):
        self.check_func = check_func

    def check(self, value):
        return self.check_func(value)