from csirtg_smrt.client.plugin import Client


class Dummy(Client):

    def __init__(self, remote, token, **kwargs):
        super(Dummy, self).__init__(remote, token)

    def indicators_create(self, data):
        if isinstance(data, dict):
            data = self._kv_to_indicator(data)

        return data

Plugin = Dummy
