from csirtg_indicator import Indicator
from csirtg_smrt.client.plugin import Client
from pyre import Pyre
import logging
from time import sleep
logger = logging.getLogger(__name__)

CHAN = 'CSIRTG'


class _Zyre(Client):

    __name__ = 'zyre'

    def __init__(self, remote=False, *args, **kwargs):
        super(_Zyre, self).__init__(remote)

    def indicators_create(self, data, **kwargs):
        if isinstance(data, dict):
            data = Indicator(**data)

        if isinstance(data, Indicator):
            data = [data]

        n = Pyre()

        n.join(CHAN)
        n.start()
        sleep(1)

        for i in data:
            n.shouts(CHAN, str(i))

        n.stop()

Plugin = _Zyre
