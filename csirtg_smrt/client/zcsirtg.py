from csirtgsdk.client import Client as CSIRTGClient
from csirtgsdk.indicator import Indicator
from csirtg_smrt.client.plugin import Client
from pprint import pprint


class _Csirtg(Client):

    def __init__(self, remote='https://csirtg.io/api', token=None, username=None, feed=None, **kwargs):
        super(_Csirtg, self).__init__(remote, token=token)

        assert username
        assert token

        self.user = username
        self.feed = feed
        self.handle = CSIRTGClient(token=token)

    def ping(self, write=False):
        return True

    def indicators_create(self, data):

        d = data.__dict__()
        d['feed'] = self.feed
        d['user'] = self.user

        i = Indicator(
            self.handle,
            d
        )

        rv = i.submit()
        print(rv)

Plugin = _Csirtg
