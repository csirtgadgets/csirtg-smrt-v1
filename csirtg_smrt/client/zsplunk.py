from csirtg_smrt.client.plugin import Client

# https://github.com/splunk/splunk-sdk-python/blob/master/examples/submit.py
class _Splunk(Client):

    __name__ = 'splunk'

    def __init__(self, remote='localhost:514', *args, **kwargs):
        super(_Splunk, self).__init__(remote)

        raise NotImplemented

    def ping(self, write=False):
        raise NotImplemented

    def indicators_create(self, data, **kwargs):
        # https://github.com/splunk/splunk-sdk-python/blob/master/examples/submit.py
        raise NotImplemented

Plugin = _Splunk
