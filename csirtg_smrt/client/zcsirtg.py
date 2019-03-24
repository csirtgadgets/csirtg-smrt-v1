from csirtgsdk.client.http import HTTP as CSIRTGClient
from csirtgsdk.indicator import Indicator
import csirtg_indicator
from csirtg_smrt.client.plugin import Client
from pprint import pprint
import os

TOKEN = os.getenv('CSIRTG_TOKEN')
USER = os.getenv('CSIRTG_USER')
FEED = os.getenv('CSIRTG_FEED')


class _Csirtg(Client):

    def __init__(self, remote='https://csirtg.io/api',
                 token=TOKEN, username=None, feed=None, **kwargs):

        if not username:
            username = USER

        if not feed:
            feed = FEED

        if not token:
            token = TOKEN

        super(_Csirtg, self).__init__(remote, token=token)

        self.user = username
        self.feed = feed

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

            i = Indicator(d)

            rv = i.submit()
            indicators.append(rv)

        assert len(indicators) > 0
        return indicators


Plugin = _Csirtg
