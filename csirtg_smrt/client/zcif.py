from cifsdk.client.http import HTTP as HTTPClient

import os

REMOTE = os.environ.get('CSIRTG_SMRT_CIF_REMOTE', 'http://localhost:5000')


class CIF(HTTPClient):

    def __init__(self, remote=None, token=None, **kwargs):
        if not remote:
            remote = REMOTE

        super(CIF, self).__init__(remote, token, **kwargs)

Plugin = CIF
