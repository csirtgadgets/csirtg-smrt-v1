from csirtgsdk.client import Client as CSIRTGClient
from csirtg_smrt.client.plugin import Client
from csirtgsdk.indicator import Indicator
from pprint import pprint


class CSIRTG(CSIRTGClient, Client):

    def __init__(self, remote, token, proxy=None, timeout=300, verify_ssl=True, user=None, feed=None, **kwargs):
        super(CSIRTG, self).__init__(remote, token)

        self.user = user
        self.feed = feed

    def ping_router(self):
        return True

    def ping(self, write=False):
        return True

    def indicators_create(self, data):
        d = data.__dict__
        d['user'] = self.user
        d['feed'] = 'test'
        del d['version']

        self.logger.info('fake submitting')
        #rv = Indicator(self, data).submit()
        pprint(d)

Plugin = CSIRTG
