import tailer  # pip install tailer
import time
import arrow  # pip install arrow
from json import loads as json_loads
import logging
import re
import os

from tzlocal import get_localzone  # pip install tzlocal
from csirtg_indicator import Indicator
from pprint import pprint
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import textwrap
from csirtg_smrt.utils import setup_logging, get_argument_parser, setup_signals
from csirtg_indicator.format import FORMATS


# this is a crappy work around for using python 2.7.6 that
# ships with Ubuntu 14.04. This is discuraged, see:
# http://urllib3.readthedocs.org/en/latest/security.html#disabling-warnings
import requests
requests.packages.urllib3.disable_warnings()

# logging configuration
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(name)s[%(lineno)s] - %(message)s'
logger = logging.getLogger('')

PROVIDER = os.environ.get('CSIRTG_SMRT_PROVIDER')

CORE_FIELDS = set('src msg time dst dpt destinationServicename'.split())

def process_line(line):
    """

    :param line: line from the input stream
    """
    try:
        record = json_loads(line)
    except ValueError:
        logger.exception("decode failed: \n{}".format(line))
        return None

    data = {
        "tags": ["scanner"],
        "indicator": record['src'],
        "description": record['msg'],
        "lasttime": record['time'],
        "firsttime": record['time'],

        "dest": record.get("dst"),
        "dest_portlist": record.get("dpt"),
        "application": record.get('destinationServicename'),
    }

    additional_data = {}
    for k, v in record.items():
        if k not in CORE_FIELDS:
            additional_data[k] = v
    if additional_data:
        data["additional_data"] = additional_data

    return Indicator(**data)

def main():
    p = get_argument_parser()
    p = ArgumentParser(
        description=textwrap.dedent('''\
            Env Variables:
                CSIRTG_RUNTIME_PATH

            example usage:
                $ csirtg-cefjson -f /var/log/foo.json.log
                $ ZYRE_GROUP=honeynet csirtg-cefjson -d -f /var/log/foo.json.log --client zyre
                $ csirtg-cefjson -f /var/log/foo.json.log --client csirtg --user wes --feed scanners -d
            '''),
        formatter_class=RawDescriptionHelpFormatter,
        prog='csirtg-cefjson',
        parents=[p],
    )

    p.add_argument('--no-verify-ssl', help='turn TLS/SSL verification OFF', action='store_true')
    p.add_argument('-f', '--file')
    p.add_argument('--client', default='stdout')
    p.add_argument('--user')
    p.add_argument('--feed')
    p.add_argument('--format', default='csv')
    p.add_argument('--provider', help='specify provider [default %(default)s]', default=PROVIDER)

    args = p.parse_args()

    if not args.provider:
        raise RuntimeError('Missing --provider flag')
    if not args.file:
        raise RuntimeError('Missing --file flag')

    # setup logging
    setup_logging(args)

    logger.debug('starting on: {}'.format(args.file))

    verify_ssl = True
    if args.no_verify_ssl:
        verify_ssl = False

    f = open(args.file)
    from csirtg_smrt import Smrt
    s = Smrt(client=args.client, username=args.user, feed=args.feed, verify_ssl=verify_ssl)

    try:
        for line in tailer.follow(f):
            i = process_line(line)
            if not i:
                logger.debug('skipping line')
                continue

            logger.debug(i)

            i.provider = args.provider

            if args.client == 'stdout':
                print(FORMATS[args.format](data=[i]))
            else:
                s.client.indicators_create(i)
                logger.info('indicator created: {}'.format(i.indicator))

    except KeyboardInterrupt:
        logger.info('SIGINT caught... stopping')
        if args.client != 'stdout':
            s.client.stop()

    logger.info('exiting...')

if __name__ == '__main__':
    main()
