from cifsdk.client.http import HTTP as HTTPClient

import os

REMOTE = os.getenv('CIF_REMOTE', 'http://localhost:5000')
TOKEN = os.getenv('CIF_TOKEN')

if REMOTE == '':
    REMOTE = 'http://localhost:5000'

if TOKEN == '':
    TOKEN = None


class CIF(HTTPClient):

    def __init__(self, remote=REMOTE, token=TOKEN, **kwargs):
        if not remote:
            remote = REMOTE

        if not token:
            token = TOKEN

        super(CIF, self).__init__(remote, token, **kwargs)

Plugin = CIF
