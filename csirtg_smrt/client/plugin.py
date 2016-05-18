from csirtg_indicator import Indicator
import abc


class Client(object):

    def __init__(self, remote, token):
        self.remote = remote
        self.token = str(token)

    def _kv_to_indicator(self, kv):
        return Indicator(**kv)

    @abc.abstractmethod
    def ping(self, write=False):
        raise NotImplementedError

    @abc.abstractmethod
    def indicator_create(self):
        raise NotImplementedError
