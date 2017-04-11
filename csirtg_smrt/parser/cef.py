import docker
import tailer  # pip install tailer
import time
import arrow  # pip install arrow
from json import loads as json_loads
import logging
import os
from csirtg_indicator import Indicator
from pprint import pprint
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import textwrap
from csirtg_smrt.utils import setup_logging, get_argument_parser, setup_signals
from csirtg_indicator.format import FORMATS

# logging configuration
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(name)s[%(lineno)s] - %(message)s'
logger = logging.getLogger('')

PROVIDER = os.environ.get('CSIRTG_SMRT_PROVIDER')

CORE_FIELDS = set('src msg time dst dpt destinationServicename'.split())


def parse_line(line):
    """

    :param line: line from the input stream
    """
    line = line.rstrip()
    if not line:
        return None
    if line.startswith('{') and line.endswith('}'):
        try:
            record = json_loads(line)
        except ValueError:
            logger.exception("decode failed: \n{}".format(line))
            return None
    else:
        record = line.split('|')
        header = record[0:6]
        ext = record[7]

        # TODO - finish
        # https://www.protect724.hpe.com/servlet/JiveServlet/downloadBody/1072-102-9-20354/CommonEventFormatv23.pdf
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

    return data


def main():
    p = get_argument_parser()
    p = ArgumentParser(
        description=textwrap.dedent('''\
            Env Variables:
                CSIRTG_RUNTIME_PATH

            example usage:
                $ csirtg-cef -f /var/log/foo.log
                $ ZYRE_GROUP=honeynet csirtg-cef -d -f /var/log/foo.log --client zyre
                $ csirtg-cef -f /var/log/foo.log --client csirtg --user wes --feed scanners -d
            '''),
        formatter_class=RawDescriptionHelpFormatter,
        prog='csirtg-cef',
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

    p.add_argument('--tail-docker')

    args = p.parse_args()

    if not args.provider:
        raise RuntimeError('Missing --provider flag')

    # setup logging
    setup_logging(args)

    verify_ssl = True
    if args.no_verify_ssl:
        verify_ssl = False

    if args.file:
        logger.debug('starting on: {}'.format(args.file))
        f = open(args.file)
        data_source = tailer.follow(f)
    elif args.tail_docker:
        logger.debug('starting on container: {}'.format(args.tail_docker))
        #data_source = subprocess.Popen(["docker", "logs", "-f", "--tail", "0", args.tail_docker], bufsize=1, stdout=subprocess.PIPE).stdout
        client = docker.from_env(version='auto')
        container = client.containers.get(args.tail_docker)
        data_source = container.logs(stream=True, follow=True, tail=0)
    else:
        raise RuntimeError('Missing --file or --tail-docker flag')

    from csirtg_smrt import Smrt
    s = Smrt(client=args.client, username=args.user, feed=args.feed, verify_ssl=verify_ssl)

    try:
        for line in data_source:
            i = parse_line(line)

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
                s.client.indicators_create(i)
                logger.info('indicator created: {}'.format(i.indicator))

    except KeyboardInterrupt:
        logger.info('SIGINT caught... stopping')
        if args.client != 'stdout':
            s.client.stop()

    logger.info('exiting...')

if __name__ == '__main__':
    main()
