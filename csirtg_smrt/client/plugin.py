from csirtg_indicator import Indicator
import abc


class Client(object):

    def __init__(self, remote, username=None, token=None):
        self.remote = remote
        self.token = token
        self.username = username

    def _kv_to_indicator(self, kv):
        return Indicator(**kv)

    def ping(self, write=False):
        return True

    @abc.abstractmethod
    def indicators_create(self, data, **kwargs):
        raise NotImplementedError
