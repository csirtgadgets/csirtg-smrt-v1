import logging
from time import sleep
logger = logging.getLogger(__name__)
import os
import names

import logging
import os.path

from csirtg_indicator import Indicator
from czmq import Zactor, zactor_fn, create_string_buffer
from time import sleep
from pyzyre.chat import task
import zmq
from pprint import pprint

GROUP = os.environ.get('ZYRE_GROUP', 'ZYRE')
INTERFACE = os.environ.get('ZSYS_INTERFACE', 'eth0')
EVASIVE_TIMEOUT = os.environ.get('ZYRE_EVASIVE_TIMEOUT', 5000)  # zyre defaults
EXPIRED_TIMEOUT = os.environ.get('ZYRE_EXPIRED_TIMEOUT', 30000)

logger = logging.getLogger()


class _Zyre(object):

    __name__ = 'zyre'

    def __init__(self, remote=False, interface=INTERFACE, group=GROUP, **kwargs):
        self.group = group
        self.interface = interface

        self.actor = None
        self._actor = None

        self.task = zactor_fn(task)

        actor_args = [
            'group=%s' % self.group,
            'beacon=1',
        ]

        if logger.getEffectiveLevel() == logging.DEBUG:
            actor_args.append('verbose=1')

        actor_args = ','.join(actor_args)
        self.actor_args = create_string_buffer(actor_args)

        logger.info('staring zyre...')

        # disable CZMQ from capturing SIGINT
        os.environ['ZSYS_SIGHANDLER'] = 'false'

        # signal zbeacon in czmq
        if not os.environ.get('ZSYS_INTERFACE'):
            os.environ["ZSYS_INTERFACE"] = self.interface

        self.start()

    def start(self):
        self._actor = Zactor(self.task, self.actor_args)
        self.actor = zmq.Socket(shadow=self._actor.resolve(self._actor).value)
        sleep(0.1)
        logger.debug('zyre started')

    def stop(self):
        logger.debug('stopping zyre')
        self.actor.send_multipart(['$$STOP', ''.encode('utf-8')])
        sleep(0.01)  # cleanup
        logger.debug('stopping zyre')
        self.actor.close()
        del self._actor

    def indicators_create(self, data, **kwargs):
        if isinstance(data, dict):
            data = Indicator(**data)

        if isinstance(data, Indicator):
            data = [data]

        for i in data:
            self.actor.send_multipart(['SHOUT', str(i).encode('utf-8')])

Plugin = _Zyre
