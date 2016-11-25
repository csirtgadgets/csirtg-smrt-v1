try:
    from pyre import Pyre
except ImportError as e:
    raise ImportError('Requires pyre')

from csirtg_indicator import Indicator
from csirtg_smrt.client.plugin import Client
import logging
from time import sleep
logger = logging.getLogger(__name__)
import os
import names

GROUP = os.environ.get('ZYRE_GROUP', 'CSIRTG')


class _Zyre(Client):

    __name__ = 'zyre'

    def __init__(self, remote=False, *args, **kwargs):
        super(_Zyre, self).__init__(remote)

        self.group = kwargs.get('group', GROUP)
        self.zyre = Pyre(names.get_full_name())
        self.zyre.start()

        sleep(1)

        self.zyre.join(self.group)

        sleep(1)

    def __exit__(self):
        self.zyre.stop()

    def __del__(self):
        self.zyre.stop()

    def indicators_create(self, data, **kwargs):
        if isinstance(data, dict):
            data = Indicator(**data)

        if isinstance(data, Indicator):
            data = [data]

        for i in data:
            self.zyre.shouts(self.group, str(i))

Plugin = _Zyre
