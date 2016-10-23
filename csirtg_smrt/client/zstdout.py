from csirtg_smrt.client.plugin import Client


class _Stdout(Client):
    __name__ = 'stdout'

    def __init__(self, remote=None, token=None, **kwargs):
        super(_Stdout, self).__init__(remote, token=token)

    def indicators_create(self, data):
        assert data
        return data.__dict__()


Plugin = _Stdout

