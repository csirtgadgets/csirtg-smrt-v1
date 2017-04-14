import logging
import os
from csirtg_indicator import Indicator
from csirtg_smrt import Smrt
from pprint import pprint
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import textwrap
from csirtg_smrt.utils import setup_logging, get_argument_parser, setup_signals
import zmq
from zmq.eventloop import ioloop
from pyzyre.client import Client, DefaultHandler
import json

# logging configuration
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(name)s[%(lineno)s] - %(message)s'
logger = logging.getLogger('')
ZSYS_INTERFACE = os.getenv('ZSYS_INTERFACE', 'eth0')
GROUP = os.getenv('ZYRE_GROUP', 'darknet')


class Handler(DefaultHandler):
    def __init__(self, client):
        self.client = client

    def on_shout(self, client, group, peer, address, message):
        logger.info(message)
        if self.client:
            i = json.loads(message)
            i = Indicator(**i)
            self.client.indicators_create(i)

    def on_whisper(self, client, peer, message):
        logger.info(message)
        if self.client:
            i = json.loads(message)
            i = Indicator(**i)
            self.client.indicators_create(i)


class ZyrePub(object):
    def __init__(self, *args, **kwargs):
        self.interface = kwargs.get('interface', ZSYS_INTERFACE)
        self.group = kwargs.get('group', GROUP)
        self.client = Client(interface=self.interface, group=self.group)
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

Plugin = ZyrePub


def main():
    p = get_argument_parser()
    p = ArgumentParser(
        description=textwrap.dedent('''\
            example usage:
                $ csirtg-zyre -d --groups honeynet,spam,darknet --client csirtg --user wes --feed honeynet
            '''),
        formatter_class=RawDescriptionHelpFormatter,
        prog='csirtg-zyre',
        parents=[p],
    )

    p.add_argument('--client', default='stdout')
    p.add_argument('--user')
    p.add_argument('--feed')
    p.add_argument('--token', default=os.getenv('CSIRTG_TOKEN'))
    p.add_argument('--no-verify-ssl', action='store_true')
    p.add_argument('-i', '--interface', default=ZSYS_INTERFACE)
    p.add_argument('-g', '--group', default='darknet')
    p.add_argument('--gossip')

    args = p.parse_args()

    verbose = False
    if args.debug:
        verbose = '1'

    # setup logging
    setup_logging(args)

    verify_ssl = True
    if args.no_verify_ssl:
        verify_ssl = False

    s = Smrt(client=args.client, username=args.user, feed=args.feed, verify_ssl=verify_ssl)

    ioloop.install()
    loop = ioloop.IOLoop.instance()

    client = Client(
        group=args.group,
        loop=loop,
        gossip_connect=args.gossip,
        verbose=verbose,
        interface=args.interface,
        handler=Handler(s.client)
    )

    client.start_zyre()

    loop.add_handler(client.actor, client.handle_message, zmq.POLLIN)

    try:
        loop.start()
    except KeyboardInterrupt:
        logger.info('SIGINT Received')

    logger.info('shutting down..')

    client.stop_zyre()

    logger.info('exiting...')

if __name__ == '__main__':
    main()
