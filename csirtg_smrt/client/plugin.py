from csirtg_indicator import Indicator
import abc


class Client(object):

    def __init__(self, remote=None, token=None, username=None):
        if remote:
            self.remote = remote

        if token:
            self.token = token

        if username:
            self.username = username

    def _kv_to_indicator(self, kv):
        return Indicator(**kv)

    def ping(self, write=False):
        return True

    @abc.abstractmethod
    def indicators_create(self, data, **kwargs):
        raise NotImplementedError
