from csirtg_smrt.utils.ztail import tail
import logging
import re
import os

from csirtg_indicator import Indicator
from pprint import pprint
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import textwrap
from csirtg_smrt.utils import setup_logging, get_argument_parser
from csirtg_indicator.format import FORMATS
from csirtg_smrt.constants import PORT_APPLICATION_MAP

import requests
requests.packages.urllib3.disable_warnings()

# usually /var/log/ufw.log
FILENAME = '/var/log/ufw.log'

# logging configuration
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(name)s[%(lineno)s] - %(message)s'
logger = logging.getLogger('')

PROVIDER = os.environ.get('CSIRTG_SMRT_PROVIDER')
RE_UFW = '^(\S+\s{1,2}\S+\s\S+)\s(\S+)\s.*UFW\s(\S+)\]\s([^,]+)$'


def _parse_tcp(record, leftover):
    record['ufw_protocol'] = 'TCP'
    record['ufw_tcp_flag_cwr'] = 0
    record['ufw_tcp_flag_ece'] = 0
    record['ufw_tcp_flag_urg'] = 0
    record['ufw_tcp_flag_ack'] = 0
    record['ufw_tcp_flag_psh'] = 0
    record['ufw_tcp_flag_rst'] = 0
    record['ufw_tcp_flag_syn'] = 0
    record['ufw_tcp_flag_fin'] = 0

    for item in leftover:
        if item.startswith('SPT'):
            record['ufw_src_port'] = item.split('=', 1)[1]
        elif item.startswith('DPT'):
            record['ufw_dst_port'] = item.split('=', 1)[1]
        elif item.startswith('WINDOW'):
            record['ufw_tcp_window'] = item.split('=', 1)[1]
        elif item.startswith('RES'):
            record['ufw_tcp_res'] = item.split('=', 1)[1]
        elif item.startswith('URGP'):
            record['ufw_tcp_urgp'] = item.split('=', 1)[1]
        elif item == "CWR":
            record['ufw_tcp_flag_cwr'] = 1
        elif item == "ECE":
            record['ufw_tcp_flag_ece'] = 1
        elif item == "URG":
            record['ufw_tcp_flag_urg'] = 1
        elif item == "ACK":
            record['ufw_tcp_flag_ack'] = 1
        elif item == "PSH":
            record['ufw_tcp_flag_psh'] = 1
        elif item == "RST":
            record['ufw_tcp_flag_rst'] = 1
        elif item == "SYN":
            record['ufw_tcp_flag_syn'] = 1
        elif item == "FIN":
            record['ufw_tcp_flag_fin'] = 1

    return record


def _parse_udp(record, leftover):
    record['ufw_protocol'] = 'UDP'

    for item in leftover:
        if item.startswith('SPT'):
            record['ufw_src_port'] = item.split('=', 1)[1]

        elif item.startswith('DPT'):
            record['ufw_dst_port'] = item.split('=', 1)[1]

        elif item.startswith('LEN'):
            record['ufw_udp_len'] = item.split('=', 1)[1]

    return record


def _parse_icmp(record, leftover):
    record['ufw_protocol'] = 'ICMP'

    for item in leftover:
        if item.startswith('TYPE'):
            record['ufw_icmp_type'] = item.split('=', 1)[1]
        elif item.startswith('CODE'):
            record['ufw_icmp_code'] = item.split('=', 1)[1]
            # need to parse out ICMP types of those are determined to be needed

    return record


def parse_line(line):
    record = {}

    # parse of entire ufw log record

    ts, hostname, action, message = re.match(RE_UFW, line).groups()

    record['ufw_timestamp'] = ts
    record['ufw_hostname'] = hostname
    record['ufw_action'] = action

    # set ufw message
    record['ufw_message'] = message

    # continue parsing ufw_message
    _r1 = re.split(r'\s+', message, 3)

    # parse layer 2 items (in, out, mac)
    base = _r1[:-1]

    # parse string after base bits
    leftover = re.split(r'\s+', _r1[-1])

    for item in base:
        if item.startswith('IN'):
            record['ufw_interface_in'] = item.split('=', 1)[1]
        elif item.startswith('OUT'):
            record['ufw_interface_out'] = item.split('=', 1)[1]
        elif item.startswith('MAC'):
            record['ufw_mac'] = item.split('=', 1)[1]

    # iterate through a copy of the leftover list
    for item in leftover[:]:
        record['ufw_ip_flag_ce'] = 0
        record['ufw_ip_flag_df'] = 0
        record['ufw_ip_flag_mf'] = 0

        if item.startswith('SRC'):
            record['ufw_src_ip'] = item.split('=', 1)[1]
        elif item.startswith('DST'):
            record['ufw_dest_ip'] = item.split('=', 1)[1]
        elif item.startswith('LEN'):
            record['ufw_ip_len'] = item.split('=', 1)[1]
        elif item.startswith('TOS'):
            record['ufw_ip_tos'] = item.split('=', 1)[1]
        elif item.startswith('PREC'):
            record['ufw_ip_prec'] = item.split('=', 1)[1]
        elif item.startswith('TTL'):
            record['ufw_ip_ttl'] = item.split('=', 1)[1]
        elif item.startswith('ID'):
            record['ufw_ip_id'] = item.split('=', 1)[1]
        elif item == "CE":
            record['ufw_ip_flag_ce'] = 1
        elif item == "DF":
            record['ufw_ip_flag_df'] = 1
        elif item == "MF":
            record['ufw_ip_flag_mf'] = 1
        else:
            continue

        leftover.remove(item)

    if leftover[0] == 'PROTO=UDP':
        record = _parse_udp(record, leftover)

    elif leftover[0] == 'PROTO=ICMP':
        record = _parse_icmp(record, leftover)

    elif leftover[0] == 'PROTO=TCP':
        record = _parse_tcp(record, leftover)

    i = {
        'indicator': record['ufw_src_ip'],
        'tags': ['scanner'],
        'description': 'iptable DROP logs',
        'portlist': record['ufw_dst_port'],
        'protocol': record['ufw_protocol'],
        'lasttime': record['ufw_timestamp'],
        'firsttime': record['ufw_timestamp']
    }

    t = PORT_APPLICATION_MAP.get(record['ufw_dst_port'])
    if t:
        i['tags'].append(t)
        i['application'] = t

    return i


def main():
    p = get_argument_parser()
    p = ArgumentParser(
        description=textwrap.dedent('''\
            Env Variables:
                CSIRTG_RUNTIME_PATH

            example usage:
                $ csirtg-ufw -f /var/log/ufw.log
                $ ZYRE_GROUP=honeynet csirtg-ufw -d -f /var/log/ufw.log --client zyre
                $ csirtg-ufw -f /var/log/ufw.log --client csirtg --user wes --feed scanners -d
            '''),
        formatter_class=RawDescriptionHelpFormatter,
        prog='csirtg-ufw',
        parents=[p],
    )

    p.add_argument('--no-verify-ssl', help='turn TLS/SSL verification OFF', action='store_true')
    p.add_argument('-f', '--file', default=FILENAME)
    p.add_argument('--client', default='stdout')
    p.add_argument('--user')
    p.add_argument('--feed')
    p.add_argument('--format', default='csv')
    p.add_argument('--provider', help='specify provider [default %(default)s]', default=PROVIDER)
    p.add_argument('--ignore-client-errors', help='skip when client errors out (eg: HTTP 5XX, etc)', action='store_true')

    args = p.parse_args()

    if not args.provider:
        raise RuntimeError('Missing --provider flag')

    # setup logging
    setup_logging(args)

    logger.debug('starting on: {}'.format(args.file))

    verify_ssl = True
    if args.no_verify_ssl:
        verify_ssl = False

    from csirtg_smrt import Smrt
    s = Smrt(client=args.client, username=args.user, feed=args.feed, verify_ssl=verify_ssl)

    try:
        for line in tail(args.file):
            logger.debug(line)

            if '[UFW BLOCK]' not in line:
                continue

            if ' SYN ' not in line:
                continue

            try:
                i = parse_line(line)

            except AttributeError:
                logger.debug("line not matched: \n{}".format(line))
                continue

            i = Indicator(**i)
            i.provider = args.provider

            if args.client == 'stdout':
                print(FORMATS[args.format](data=[i]))
                continue

            try:
                s.client.indicators_create(i)
                logger.info('indicator created: {}'.format(i.indicator))

            except Exception as e:
                logger.error(e)
                if args.ignore_client_errors:
                    pass

    except KeyboardInterrupt:
        logger.info('SIGINT caught... stopping')
        if args.client != 'stdout':
            try:
                s.client.stop()
            except AttributeError:
                pass

    logger.info('exiting...')

if __name__ == '__main__':
    main()
