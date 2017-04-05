
class CsirtgException(Exception):
    def __init__(self, msg):
        self.msg = "{}".format(msg)

    def __str__(self):
        return self.msg


class AuthError(CsirtgException):
    pass


class TimeoutError(CsirtgException):
    pass


class RuleUnsupported(CsirtgException):
    pass


class SubmissionFailure(CsirtgException):
    pass
