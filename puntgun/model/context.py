from puntgun.model.user import User


class Context(object):
    """
    DTO, information collection passed between rules and is used as
    the input value of the rule judgment logic.

    One instance represent one potential user's information.
    """

    def __init__(self, user: User):
        self.user_id = user.id
        self.user = user
