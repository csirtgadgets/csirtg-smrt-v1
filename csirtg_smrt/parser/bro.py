from csirtg_smrt.utils.ztail import tail
from json import loads as json_loads
import logging
import os
from csirtg_indicator import Indicator
from pprint import pprint
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import textwrap
from csirtg_smrt.utils import setup_logging, get_argument_parser
from csirtg_indicator.format import FORMATS
import re
# logging configuration
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(name)s[%(lineno)s] - %(message)s'
logger = logging.getLogger('')

PROVIDER = os.environ.get('CSIRTG_SMRT_PROVIDER')

# https://github.com/JustinAzoff/bro-pdns/blob/master/bro_pdns.py#L27
CORE_FIELDS = set('src ts dst'.split())


class BroTailer(object):

    def __init__(self, file, json=False, **kwargs):
        self.headers = {}

        with open(file) as _file:
            line = ''
            it = iter(_file)

            while not line.startswith("#types"):
                line = next(it).rstrip()
                k, v = line[1:].split(None, 1)
                self.headers[k] = v

            self.sep = self.headers['separator'].encode('utf-8').decode("unicode_escape")

            for k, v in self.headers.items():
                if self.sep in v:
                    self.headers[k] = v.split(self.sep)

            self.headers['separator'] = self.sep
            self.fields = self.headers['fields']
            self.types = self.headers['types']
            self.set_sep = self.headers['set_separator']
            self.vectors = [field for field, type in zip(self.fields, self.types) if type.startswith("vector[")]

    def parse_line(self, line):
        if line.startswith("#close"):
            return

        if not len(line):
            return

        parts = line.rstrip().split(self.sep)

        record = dict(zip(self.fields, parts))

        for k in record:
            if record[k] == '-':
                record[k] = None

        for f in self.vectors:
            record[f] = record[f].split(self.set_sep)

        description = "{note}: {msg}".format(**record)
        data = {
            "indicator": record['src'],
            "description": description,
            "lasttime": record['ts'],
            "firsttime": record['ts'],
        }

        if record.get('dest'):
            data["dest"] = record.get("dst")

        additional_data = {}
        for k, v in record.items():
            if k not in CORE_FIELDS:
                if v is not None:
                    additional_data[k] = v

        if additional_data:
            data["additional_data"] = additional_data

        return data


def main():
    p = get_argument_parser()
    p = ArgumentParser(
        description=textwrap.dedent('''\
            Env Variables:
                CSIRTG_RUNTIME_PATH

            example usage:
                $ csirtg-bro -f /var/log/foo.log
                $ ZYRE_GROUP=honeynet csirtg-bro -d -f /var/log/foo.log --client zyre
                $ csirtg-bro -f /var/log/foo.log --client csirtg --user wes --feed scanners -d
            '''),
        formatter_class=RawDescriptionHelpFormatter,
        prog='csirtg-bro',
        parents=[p],
    )

    p.add_argument('--no-verify-ssl', help='turn TLS/SSL verification OFF', action='store_true')
    p.add_argument('-f', '--file')
    p.add_argument('--client', default='stdout')
    p.add_argument('--user')
    p.add_argument('--feed')
    p.add_argument('--format', default='csv')
    p.add_argument('--tags', help='specify indicator tags [default %(default)s', default='scanner')
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

    from csirtg_smrt import Smrt
    s = Smrt(client=args.client, username=args.user, feed=args.feed, verify_ssl=verify_ssl)

    b = BroTailer(args.file)

    try:
        for l in tail(args.file):
            if l.startswith('#'):
                continue

            i = b.parse_line(l)

            if not i:
                logger.debug('skipping line')
                continue

            i = Indicator(**i)

            logger.debug(i)

            i.provider = args.provider
            i.tags = args.tags

            if args.client == 'stdout':
                print(FORMATS[args.format](data=[i]))
            else:
                try:
                    s.client.indicators_create(i)
                    logger.info('indicator created: {}'.format(i.indicator))
                except Exception as e:
                    logger.error(e)

    except Exception as e:
        logger.error(e)

    except KeyboardInterrupt:
        logger.info('SIGINT caught... stopping')
        if args.client != 'stdout':
            s.client.stop()

    logger.info('exiting...')

if __name__ == '__main__':
    main()
