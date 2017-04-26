import asyncore
from smtpd import SMTPServer
import logging
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import textwrap
import os
import json
from pprint import pprint
import arrow
from datetime import datetime
from csirtg_smrt.smrt import Smrt
from csirtg_indicator.indicator import Indicator
#from csirtg_smrt.utils import setup_logging, get_argument_parser, setup_signals
#from csirtg_indicator.format import FORMATS
import socket

# logging configuration
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(name)s[%(lineno)s] - %(message)s'
logger = logging.getLogger('')

PROVIDER = os.environ.get('CSIRTG_SMRT_SMTP_PROVIDER', socket.gethostname())
INTERFACE = os.getenv('ZSYS_INTERFACE', 'eth0')
ZYRE_GROUP = os.getenv('ZYRE_GROUP', 'spam')

# https://pymotw.com/2/smtpd/
# https://docs.python.org/3/library/smtpd.html
class EmlServer(SMTPServer):
    client = None
    no = 0
    log_message = None

    def process_message(self, peer, mailfrom, rcpttos, data):
        if self.log_message:
            filename = '%s/%s-%d.eml' % (self.log_message, datetime.now().strftime('%Y%m%d%H%M%S'), self.no)
            f = open(filename, 'w')
            f.write(data)
            f.close
            logger.info('%s saved.' % filename)

        m = {
            'peer': peer,
            'mailfrom': mailfrom,
            'rcpttos': rcpttos,
            'data': data
        }
        logger.debug('{}'.format(json.dumps(m, indent=4)))
        ts = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%sZ')
        i = Indicator(
            indicator=peer[0],
            tags=['smtp', 'spam', 'relay'],
            description='peer using open smtp relay',
            provider=PROVIDER,
            portlist=25,
            message=data,
            lasttime=ts,
            firsttime=ts,
            reporttime=ts,
            additional_data={
                'from': mailfrom,
                'recpttos': rcpttos,
                'src_portlist': peer[1],
            }
        )

        logger.debug(i)
        if self.client:
            self.client.indicators_create(i)

        self.no += 1


def main():
    p = ArgumentParser(
        description=textwrap.dedent('''\
                example usage:
                    $ csirtg-smtpd
                    $ ZYRE_GROUP=honeynet csirtg-smtod --port 2525
                '''),
        formatter_class=RawDescriptionHelpFormatter,
        prog='csirtg-smtpd',
    )

    p.add_argument('--client', default='stdout')
    p.add_argument('--port', help='specify smtp listener port', default=2525)
    p.add_argument('--listen', default='localhost')
    p.add_argument('--interface', default=INTERFACE)
    p.add_argument('--group', default=ZYRE_GROUP)
    p.add_argument('-d', '--debug', action='store_true')
    p.add_argument('--log')
    p.add_argument('--remote')
    p.add_argument('--user')
    p.add_argument('--feed')
    p.add_argument('--token')

    args = p.parse_args()

    loglevel = logging.INFO
    verbose = False
    if args.debug:
        loglevel = logging.DEBUG
        verbose = '1'

    console = logging.StreamHandler()
    logging.getLogger('').setLevel(loglevel)
    console.setFormatter(logging.Formatter(LOG_FORMAT))
    logging.getLogger('').addHandler(console)
    logging.propagate = False

    logger.info('starting listener: {}:{}'.format(args.listen, args.port))
    server = EmlServer((args.listen, int(args.port)), None)
    if args.log:
        logger.info('logging messages to: {}'.format(args.log))
        server.log_message = args.log

    if args.client != 'stdout':
        s = Smrt(remote=args.remote, token=args.token, username=args.user, client=args.client, feed=args.feed)
        server.client = s.client
        server.client.start()

    try:
        asyncore.loop()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
