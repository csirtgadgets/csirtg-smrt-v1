import tailer  # pip install tailer
import time
import arrow  # pip install arrow
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

# usually /var/log/ufw.log
filename = '/var/log/ufw.log'

# logging configuration
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(name)s[%(lineno)s] - %(message)s'
logger = logging.getLogger('')

PROVIDER = os.environ.get('CSIRTG_SMRT_PROVIDER')

PORT_APPLICATION = {
    '21': 'ftp',
    '22': 'ssh',
    '23': 'telnet',
    '80': 'http',
    '443': 'https',
    '3306': 'mysql',
    '5900': 'vnc',
    '3389': 'rdp'
}


def _split_equal(item):
    """
    This function takes in a value in teh form <key>=<value> and returns the value

    :param item: (eg: SRC=141.212.121.155)
    :return: value [str]
    """
    result = item.rsplit('=', 1)
    return result[1]


def normalize_syslog_timestamp(syslog_timestamp, time_now, local_tz):
    """
    Return a timestamp with the correct year and in UTC from a syslog timestamp
    :return: string (ex: 2015-11-11T21:15:29-0000)

    Reference:
    https://github.com/logstash-plugins/logstash-filter-date/pull/4/files
    https://github.com/jsvd/logstash-filter-date/blob/cfd8949e94ed0760434e3c9a9ff3da5351b4fd59/lib/logstash/filters/date.rb#L189
    """

    # get the current month
    now_month = time_now.month

    # semi normalize syslog timestamp
    syslog_timestamp_obj = arrow.get(syslog_timestamp, ['MMM  D HH:mm:ss', 'MMM D HH:mm:ss'])

    # get the month of the syslog timestamp
    event_month = syslog_timestamp_obj.month

    # calculate event year based on current month and event month
    if event_month == now_month:
        event_year = time_now.year
    elif event_month == 12 and now_month == 1:
        event_year = (time_now.year - 1)
    elif event_month == 1 and now_month == 12:
        event_year = (time_now.year + 1)
    else:
        event_year = time_now.year

    # update event year based on calculated result and local timezone
    syslog_timestamp_obj = syslog_timestamp_obj.replace(year=event_year, tzinfo=local_tz.zone)

    return syslog_timestamp_obj.to('UTC').format('YYYY-MM-DDTHH:mm:ssZ')


def parse_record(line):
    """
    Parse a single ufw firewall log record using regular expressions and return a single dictionary

    :param line: single ufw firwall log record
    :return: dictionary
    """

    record = {}

    # parse of entire ufw log record
    #RE_UFW = "^(\S+\s\S+\s\S+)\s(\S+)\s\S+\s\[[^,]+\]\s\[UFW\s(\S+)\]\s([^,]+)$"
    RE_UFW = '^(\S+\s{1,2}\S+\s\S+)\s(\S+)\s\S+\s\[[\s+]?[^,]+\]\s\[UFW\s(\S+)\]\s([^,]+)$'
    ts, hostname, action, message = re.match(RE_UFW, line).groups()

    record['ufw_timestamp'] = ts
    # set hostname
    record['ufw_hostname'] = hostname

    record['ufw_action'] = action

    # set ufw message
    record['ufw_message'] = message

    # parse ufw_message bits
#    m = re.match('\[UFW\s(\S+)\]\s(.*)', record['ufw_message'])
#    # set ufw action
#    record['ufw_action'] = m.group(1)

    # continue parsing ufw_message
    _r1 = re.split(r'\s+', message, 3)
#    pprint(_r1)
#    raise

    # parse layer 2 items (in, out, mac)
    base = _r1[:-1]

    # parse string after base bits
    leftover = re.split(r'\s+', _r1[-1])

    #pprint(leftover)

    for item in base:
        if item.startswith('IN'):
            record['ufw_interface_in'] = _split_equal(item)
        elif item.startswith('OUT'):
            record['ufw_interface_out'] = _split_equal(item)
        elif item.startswith('MAC'):
            record['ufw_mac'] = _split_equal(item)

    #print(leftover)

    # iterate through a copy of the leftover list
    for item in leftover[:]:
        record['ufw_ip_flag_ce'] = 0
        record['ufw_ip_flag_df'] = 0
        record['ufw_ip_flag_mf'] = 0

        if item.startswith('SRC'):
            record['ufw_src_ip'] = _split_equal(item)
        elif item.startswith('DST'):
            record['ufw_dest_ip'] = _split_equal(item)
        elif item.startswith('LEN'):
            record['ufw_ip_len'] = _split_equal(item)
        elif item.startswith('TOS'):
            record['ufw_ip_tos'] = _split_equal(item)
        elif item.startswith('PREC'):
            record['ufw_ip_prec'] = _split_equal(item)
        elif item.startswith('TTL'):
            record['ufw_ip_ttl'] = _split_equal(item)
        elif item.startswith('ID'):
            record['ufw_ip_id'] = _split_equal(item)
        elif item == "CE":
            record['ufw_ip_flag_ce'] = 1
        elif item == "DF":
            record['ufw_ip_flag_df'] = 1
        elif item == "MF":
            record['ufw_ip_flag_mf'] = 1
        else:
            continue

        leftover.remove(item)

    # parse out protocols
    if leftover[0] == 'PROTO=TCP':
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
                record['ufw_src_port'] = _split_equal(item)
            elif item.startswith('DPT'):
                record['ufw_dst_port'] = _split_equal(item)
            elif item.startswith('WINDOW'):
                record['ufw_tcp_window'] = _split_equal(item)
            elif item.startswith('RES'):
                record['ufw_tcp_res'] = _split_equal(item)
            elif item.startswith('URGP'):
                record['ufw_tcp_urgp'] = _split_equal(item)
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

    elif leftover[0] == 'PROTO=UDP':
        record['ufw_protocol'] = 'UDP'

        for item in leftover:
            if item.startswith('SPT'):
                record['ufw_src_port'] = _split_equal(item)

            elif item.startswith('DPT'):
                record['ufw_dst_port'] = _split_equal(item)

            elif item.startswith('LEN'):
                record['ufw_udp_len'] = _split_equal(item)

    elif leftover[0] == 'PROTO=ICMP':
        record['ufw_protocol'] = 'ICMP'

        for item in leftover:
            if item.startswith('TYPE'):
                record['ufw_icmp_type'] = _split_equal(item)
            elif item.startswith('CODE'):
                record['ufw_icmp_code'] = _split_equal(item)
            # need to parse out ICMP types of those are determined to be needed

    return record


def process_events(events):
    """

    :param events: list - list of records from ufw.log
    :return [int] number of records sent
    """

    sent_count = 0

    # get local timezone
    local_tz = get_localzone()

    # Initiate wf client object
    # get now time object based on local timezone
    time_now = arrow.get(get_localzone())

    for line in events:
        record = []
        try:
            record = parse_record(line)
        except AttributeError:
            logger.debug("line not matched: \n{}".format(line))
            yield
            continue

        normalized_timestamp = normalize_syslog_timestamp(record['ufw_timestamp'], time_now, local_tz)

        if record['ufw_action'] != 'BLOCK':
            yield
            continue

        if record['ufw_protocol'] != 'TCP':
            yield
            continue

        if record['ufw_tcp_flag_syn'] != 1:
            yield
            continue

        data = {
            "indicator": record['ufw_src_ip'],
            "tags": ["scanner"],
            "description": "sourced from firewall logs (incomming, TCP, Syn, blocked)",
            "portlist": record['ufw_dst_port'],
            "protocol": record['ufw_protocol'],
            "lasttime": normalized_timestamp,
            "firsttime": normalized_timestamp
        }

        t = PORT_APPLICATION.get(record['ufw_dst_port'])
        if t:
            data['tags'].append(t)
            data['application'] = t

        yield Indicator(**data)


def main():
    p = get_argument_parser()
    p = ArgumentParser(
        description=textwrap.dedent('''\
            Env Variables:
                CSIRTG_RUNTIME_PATH

            example usage:
                $ csirtg-ufw -f /var/log/ufw.log
                $ ZYRE_GROUP=honeynet csirtg-ufw -d -f /var/log/ufw.log
                $ csirtg-ufw -f /var/log/ufw.log --client csirtg --user wes --feed scanners -d
            '''),
        formatter_class=RawDescriptionHelpFormatter,
        prog='csirtg-ufw',
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
            logger.debug(line)
            i = next(process_events([line]))
            if not i:
                logger.debug('skipping line')
                continue

            i = i.__dict__()

            if args.client == 'stdout':
                print(FORMATS[args.format](data=[i]))
            else:
                s.client.indicators_create(i)
                logger.info('indicator created: {}'.format(i['indicator']))

    except KeyboardInterrupt:
        logger.info('SIGINT caught... stopping')
        if args.client != 'stdout':
            s.client.stop()

    logger.info('exiting...')

if __name__ == '__main__':
    main()
