from cifsdk.client.http import HTTP as HTTPClient


class CIF(HTTPClient):

    def __init__(self, **kwargs):
        super(CIF, self).__init__(**kwargs)

    def ping(self, write=True):
        return self.ping_write()


Plugin = CIF
