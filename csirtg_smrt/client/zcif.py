from cifsdk.client.http import HTTP as HTTPClient


class CIF(HTTPClient):

    def __init__(self, remote=None, token=None, **kwargs):
        if not remote:
            remote = 'http://localhost:5000'

        super(CIF, self).__init__(remote, token, **kwargs)

Plugin = CIF
