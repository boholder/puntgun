class Report(object):
    """
    Report classes are kind of text formatting wrapper for saving business operation records
    into final report file, for user reviewing and record saving.

    While Actions are the final step of judgement operation pipeline,
    there is no more business operations
    (and operation results, for both successes and errors) after it,
    We'll let Actions to generate Report instances after their execution.

    Report instances flow from Actions to HuntingPlan,
    where they will be saved into the file.
    """

    pass


class ExecutionReport(Report):
    """
    Action generates an ExecutionReport instance
    after executed (block|mute) operation on one user,
    describing {which user} triggered {what rule}, and {the result of execution}.
    """

    pass


class ErrorReport(Report):
    """
    Wrapper for formatting business errors' (e.g. TwitterApiError) content.
    """

    pass
