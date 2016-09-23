from cifsdk.client.zeromq import ZMQ as ZMQClient
from csirtg_smrt.constants import ROUTER_ADDR


class CIF(ZMQClient):

    def __init__(self, remote=ROUTER_ADDR, token=None, **kwargs):
        if not remote:
            remote = ROUTER_ADDR

        super(CIF, self).__init__(remote, token, **kwargs)

Plugin = CIF

