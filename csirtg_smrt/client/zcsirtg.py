from csirtgsdk.client import Client as CSIRTGClient
from csirtgsdk.indicator import Indicator
import csirtg_indicator
from csirtg_smrt.client.plugin import Client
from pprint import pprint
import os

TOKEN = os.environ.get('CSIRTG_TOKEN')


class _Csirtg(Client):

    def __init__(self, remote='https://csirtg.io/api', token=TOKEN, username=None, feed=None, **kwargs):
        super(_Csirtg, self).__init__(remote, token=token)

        assert username
        assert token

        self.user = username
        self.feed = feed
        self.handle = CSIRTGClient(token=token)

    def start(self):
        return True

    def stop(self):
        return True

    def indicators_create(self, data):

        if not isinstance(data, list):
            data = [data]

        indicators = []
        for x in data:
            d = {}

            if isinstance(x, csirtg_indicator.Indicator):
                d = x.__dict__()
            else:
                d = x
            
            d['feed'] = self.feed
            d['user'] = self.user

            i = Indicator(
                self.handle,
                d
            )

            rv = i.submit()
            indicators.append(rv)

        assert len(indicators) > 0
        return indicators

Plugin = _Csirtg
