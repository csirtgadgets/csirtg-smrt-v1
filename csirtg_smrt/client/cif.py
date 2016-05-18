from cifsdk.client.http import HTTP as HTTPClient


class CIF(HTTPClient, Client):

    def __init__(self, remote, token, proxy=None, timeout=300, verify_ssl=True, **kwargs):
        super(CIF, self).__init__(remote, token)


Plugin = CIF