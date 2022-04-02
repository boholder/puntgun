"""Various specific errors for this project."""
from typing import List


class TwitterClientError(Exception):
    """Class for wrapping all Twitter client library custom errors."""

    def __init__(self, client_error: Exception):
        super().__init__(client_error)
        self.real_error = client_error


class TwitterApiErrors(Exception):
    """
    Error raised when a Twitter Dev API call returns http status code 200,
    but has an "errors" field in the response body,
    which indicates several "Partial error" occurs
    and the result is not completely what we expected.

    https://developer.twitter.com/en/support/twitter-api/error-troubleshooting#partial-errors

    Contains a list of errors returned by Twitter API.
    """

    def __init__(self, resp_errors: List[dict]):
        self.errors = [TwitterApiError.build_from_response(e) for e in resp_errors]
        super().__init__(f"Twitter API returned partial errors: {self.errors}")

    def __bool__(self):
        return bool(self.errors)

    def __len__(self):
        return len(self.errors)

    def __iter__(self):
        return iter(self.errors)

    def __getitem__(self, index):
        return self.errors[index]


class TwitterApiError(Exception):
    title = 'generic twitter api error'

    def __init__(self, title, ref_url, detail, parameter, value):
        super().__init__(f'{detail} Refer: {ref_url}.')
        self.title = title
        self.ref_url = ref_url
        self.detail = detail
        self.parameter = parameter
        self.value = value

    @staticmethod
    def build_from_response(resp_error: dict):
        # build an accurate error type according to the response content
        for subclass in TwitterApiError.__subclasses__():
            if subclass.title == resp_error['title']:
                return subclass(
                    title=resp_error['title'],
                    ref_url=resp_error['type'],
                    detail=resp_error['detail'],
                    parameter=resp_error['parameter'],
                    value=resp_error['value'])

        # if we haven't written a subclass for given error, return generic error
        return TwitterApiError(
            title=resp_error['title'],
            ref_url=resp_error['type'],
            detail=resp_error['detail'],
            parameter=resp_error['parameter'],
            value=resp_error['value'])


class ResourceNotFoundError(TwitterApiError):
    """
    For example, if you try to query info about a not exist user id,
    this error will be raised.
    """
    title = 'Not Found Error'
