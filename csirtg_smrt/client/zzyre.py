import logging
from time import sleep
logger = logging.getLogger(__name__)

import logging
import os.path

from csirtg_indicator import Indicator
from pyzyre.client import Client as ZyreClient
from pprint import pprint

GROUP = os.environ.get('ZYRE_GROUP', 'ZYRE')
INTERFACE = os.environ.get('ZSYS_INTERFACE', 'eth0')

logger = logging.getLogger()


class _Zyre(object):

    __name__ = 'zyre'

    def __init__(self, *args, **kwargs):
        self.interface = kwargs.get('interface', INTERFACE)
        self.group = kwargs.get('group', GROUP)
        self.client = ZyreClient(interface=self.interface, group=self.group)
        self.start()

    def start(self):
        self.client.start_zyre()

    def stop(self):
        self.client.stop_zyre()

    def indicators_create(self, data):
        if isinstance(data, dict):
            data = Indicator(**data)

        if isinstance(data, Indicator):
            data = [data]

        for i in data:
            self.client.shout(self.group, str(i))

Plugin = _Zyre
