#!/usr/bin/env python

import logging
import os.path
import textwrap
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import itertools
from random import randint
from time import sleep
from pprint import pprint
import traceback
import sys
import select
import arrow
from multiprocessing import Process
import tornado.ioloop as ioloop

import csirtg_smrt.parser
from csirtg_smrt.archiver import Archiver, NOOPArchiver
import csirtg_smrt.client
from csirtg_indicator.constants import COLUMNS
from csirtg_smrt.constants import REMOTE_ADDR, SMRT_RULES_PATH, SMRT_CACHE, CONFIG_PATH, RUNTIME_PATH, VERSION, FIREBALL_SIZE, CACHE_PATH
from csirtg_smrt.rule import Rule
from csirtg_smrt.fetcher import Fetcher
from csirtg_smrt.utils import setup_logging, get_argument_parser, load_plugin, setup_signals, read_config, \
    setup_runtime_path, chunk
from csirtg_smrt.exceptions import AuthError, TimeoutError, RuleUnsupported, SubmissionFailure
from csirtg_indicator.format import FORMATS
from csirtg_indicator import Indicator
from csirtg_indicator.exceptions import InvalidIndicator
from csirtg_indicator.utils import normalize_itype


PARSER_DEFAULT = "pattern"
TOKEN = os.environ.get('CSIRTG_SMRT_TOKEN')
ARCHIVE_PATH = os.environ.get('CSIRTG_SMRT_ARCHIVE_PATH', CACHE_PATH)
ARCHIVE_PATH = os.path.join(ARCHIVE_PATH, 'smrt.db')
FORMAT = os.environ.get('CSIRTG_SMRT_FORMAT', 'table')
SERVICE_INTERVAL = os.environ.get('CSIRTG_SMRT_SERVICE_INTERVAL', 60)
GOBACK_DAYS = os.environ.get('CSIRTG_SMRT_GOBACK_DAYS', False)
STDOUT_FIELDS = COLUMNS


# http://python-3-patterns-idioms-test.readthedocs.org/en/latest/Factory.html
# https://gist.github.com/pazdera/1099559
logging.getLogger("requests").setLevel(logging.WARNING)

if os.getenv('CSIRTG_SMRT_HTTP_TRACE', '0') == '0':
    logging.getLogger("requests.packages.urllib3.connectionpool").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class Smrt(object):
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __enter__(self):
        return self

    def __init__(self, token=TOKEN, remote=REMOTE_ADDR, client='stdout', username=None, feed=None, archiver=None,
                 fireball=False, no_fetch=False, verify_ssl=True, goback=False, skip_invalid=False, send_retries=5,
                 send_retries_wait=30):

        self.logger = logging.getLogger(__name__)

        self.client = None
        if client != 'stdout':
            plugin_path = os.path.join(os.path.dirname(__file__), 'client')
            if getattr(sys, 'frozen', False):
                plugin_path = os.path.join(sys._MEIPASS, 'csirtg_smrt', 'client')

            self.client = load_plugin(plugin_path, client)

            if not self.client:
                raise RuntimeError("Unable to load plugin: {}".format(client))

            self.client = self.client(remote=remote, token=token, username=username, feed=feed, fireball=fireball,
                                      verify_ssl=verify_ssl)

        self.archiver = archiver or NOOPArchiver()
        self.fireball = fireball
        self.no_fetch = no_fetch
        self.goback = goback
        self.skip_invalid = skip_invalid
        self.verify_ssl = verify_ssl
        self.last_cache = None
        self.send_retries = send_retries
        self.send_retries_wait = send_retries_wait

    def is_archived(self, indicator):
        return self.archiver.search(indicator)

    def archive(self, indicator):
        return self.archiver.create(indicator)

    def load_feeds(self, rule, feed=None):
        if isinstance(rule, str) and os.path.isdir(rule):
            for f in sorted(os.listdir(rule)):
                if f.startswith('.'):
                    continue

                if os.path.isdir(f):
                    continue

                self.logger.info("processing {0}/{1}".format(rule, f))
                try:
                    r = Rule(path=os.path.join(rule, f))
                except RuleUnsupported as e:
                    logger.error(e)
                    continue

                for feed in r.feeds:
                    yield r, feed

        else:
            self.logger.info("processing {0}".format(rule))
            if isinstance(rule, str):
                try:
                    rule = Rule(path=rule)
                except RuleUnsupported as e:
                    logger.error(e)
                    return

            if feed:
                # replace the feeds dict with the single feed
                # raises KeyError if it doesn't exist
                rule.feeds = {feed: rule.feeds[feed]}

            for f in rule.feeds:
                yield rule, f

    def load_parser(self, rule, feed, limit=None, data=None, filters=None):
        if isinstance(rule, str):
            rule = Rule(rule)

        fetch = Fetcher(rule, feed, data=data, no_fetch=self.no_fetch, verify_ssl=self.verify_ssl, limit=limit)
        self.last_cache = fetch.cache

        parser_name = rule.feeds[feed].get('parser') or rule.parser or PARSER_DEFAULT

        if not parser_name:
            from csirtg_smrt.utils.zcontent import get_type
            try:
                parser_name = get_type(self.last_cache)
            except Exception as e:
                logger.error(e)

        if not parser_name:
            parser_name = PARSER_DEFAULT

        plugin_path = os.path.join(os.path.dirname(__file__), 'parser')

        if getattr(sys, 'frozen', False):
            plugin_path = os.path.join(sys._MEIPASS, plugin_path)

        parser = load_plugin(plugin_path, parser_name)

        if parser is None:
            self.logger.info('trying z{}'.format(parser_name))
            parser = load_plugin(csirtg_smrt.parser.__path__[0], 'z{}'.format(parser_name))
            if parser is None:
                raise SystemError('Unable to load parser: {}'.format(parser_name))

        self.logger.debug("loading parser: {}".format(parser))

        return parser(self.client, fetch, rule, feed, limit=limit, filters=filters, fireball=self.fireball)

    def clean_indicator(self, i, rule):
        # check for de-fang'd feed
        if rule.replace:
            for e in i:
                if not rule.replace.get(e):
                    continue

                for k, v in rule.replace[e].items():
                    i[e] = i[e].replace(k, v)

        i = normalize_itype(i)

        if isinstance(i, dict):
            i = Indicator(**i)

        if not i.firsttime:
            i.firsttime = i.lasttime

        if not i.reporttime:
            i.reporttime = arrow.utcnow().datetime

        if not i.group:
            i.group = 'everyone'

        return i

    def is_archived_with_log(self, i):
        if self.is_archived(i):
            self.logger.debug('skipping: {}/{}/{}/{}'.format(i.indicator, i.provider, i.firsttime, i.lasttime))
            return True
        else:
            self.logger.debug('adding: {}/{}/{}/{}'.format(i.indicator, i.provider, i.firsttime, i.lasttime))
            return False

    def is_old(self, i):
        if i.lasttime is None:
            return

        if i.lasttime < self.goback:
            return True

    def is_valid(self, i, rule):
        # check for de-fang'd feed
        if not i.get('indicator') or i['indicator'] == '':
            return False

        if rule.replace:
            for e in i:
                if not rule.replace.get(e):
                    continue

                for k, v in rule.replace[e].items():
                    i[e] = i[e].replace(k, v)

        try:
            i = normalize_itype(i)
            return True
        except InvalidIndicator as e:
            if logger.getEffectiveLevel() == logging.DEBUG:
                if not self.skip_invalid:
                    raise e
            return False

    def _send_indicators(self, indicators):
        n = int(self.send_retries) - 1
        s = int(self.send_retries_wait)
        success = False
        while n > 0:
            try:
                self.client.indicators_create(indicators)
                n = 0
                success = True
            except Exception as e:
                logger.error('delay trying to submit indicators')
                logger.error(e)
                logger.info('[{} / {}] waiting {}s for retry...'.format((int(self.send_retries) - n), self.send_retries, s))
                n -= 1
                sleep(s)

        if not success:
            raise SubmissionFailure('unable reach remote node')

    def send_indicators(self, indicators):
        if not self.client:
            return

        if self.fireball:
            self.logger.debug('flushing queue...')
            self._send_indicators(indicators)
            return

        for i in indicators:
            self._send_indicators(i)
    
    def process(self, rule, feed, limit=None, data=None, filters=None):
        parser = self.load_parser(rule, feed, limit=limit, data=data, filters=filters)

        feed_indicators = parser.process()

        if not limit:
            limit = rule.feeds[feed].get('limit')

        if limit:
            feed_indicators = itertools.islice(feed_indicators, int(limit))

        feed_indicators = (i for i in feed_indicators if self.is_valid(i, rule))
        feed_indicators = (self.clean_indicator(i, rule) for i in feed_indicators)

        # check to see if the indicator is too old
        if self.goback:
            feed_indicators = (i for i in feed_indicators if not self.is_old(i))
        
        feed_indicators = (i for i in feed_indicators if not self.is_archived_with_log(i))

        feed_indicators_batches = chunk(feed_indicators, int(FIREBALL_SIZE))

        for indicator_batch in feed_indicators_batches:
            self.archiver.begin()
            self.send_indicators(indicator_batch)

            for i in indicator_batch:
                if self.is_archived_with_log(i):
                    continue

                yield i.format_keys()
                self.archive(i)

            self.archiver.commit()

        if limit:
            self.logger.debug("limit reached...")


def _run_smrt(options, **kwargs):
    args = kwargs.get('args')
    goback = kwargs.get('goback')
    verify_ssl = kwargs.get('verify_ssl')
    data = kwargs.get('data')
    service_mode = kwargs.get("service_mode")

    archiver = None
    if args.remember:
        archiver = Archiver(dbfile=args.remember_path)
    else:
        archiver = NOOPArchiver()

    logger.info('starting run...')

    with Smrt(options.get('token'), options.get('remote'), client=args.client, username=args.user,
              feed=args.feed, archiver=archiver, fireball=args.fireball, no_fetch=args.no_fetch,
              verify_ssl=verify_ssl, goback=goback, skip_invalid=args.skip_invalid, send_retries=args.send_retries,
              send_retries_wait=args.send_retries_wait) as s:

        if s.client:
            s.client.ping(write=True)

        filters = {}
        if args.filter_indicator:
            filters['indicator'] = args.filter_indicator

        indicators = []
        for r, f in s.load_feeds(args.rule, feed=args.feed):
            logger.info('processing: {} - {}:{}'.format(args.rule, r.defaults['provider'], f))
            try:
                for i in s.process(r, f, limit=args.limit, data=data, filters=filters):
                    if args.client == 'stdout':
                        indicators.append(i)
            except Exception as e:
                if not service_mode and not args.skip_broken:
                    logger.error('may need to remove the old cache file: %s' % s.last_cache)
                    import traceback
                    logger.error(traceback.print_exc())
                    raise e

                logger.error(e)
                logger.info('skipping: {}'.format(args.feed))

        if args.client == 'stdout':
            print(FORMATS[options.get('format')](data=indicators, cols=args.fields.split(',')))

    logger.info('cleaning up')
    archiver.cleanup()
    archiver.clear_memcache()

    logger.info('finished run')


def main():
    p = get_argument_parser()
    p = ArgumentParser(
        description=textwrap.dedent('''\
        Env Variables:
            CSIRTG_RUNTIME_PATH
            CSIRTG_SMRT_TOKEN

        example usage:
            $ csirtg-smrt --rule rules/default
            $ csirtg-smrt --rule default/csirtg.yml --feed port-scanners --remote http://localhost:5000
        '''),
        formatter_class=RawDescriptionHelpFormatter,
        prog='csirtg-smrt',
        parents=[p],
    )

    p.add_argument("-r", "--rule", help="specify the rules directory or specific rules file [default: %(default)s",
                   default=SMRT_RULES_PATH)

    p.add_argument("-f", "--feed", help="specify the feed to process")

    p.add_argument("--remote", help="specify the remote api url")
    p.add_argument('--remote-type', help="specify remote type [cif, csirtg, elasticsearch, syslog, etc]")
    p.add_argument('--client', default='stdout')

    p.add_argument('--cache', help="specify feed cache [default %(default)s]", default=SMRT_CACHE)

    p.add_argument("--limit", help="limit the number of records processed [default: %(default)s]",
                   default=None)

    p.add_argument("--token", help="specify token [default: %(default)s]", default=TOKEN)

    p.add_argument('--service', action='store_true', help="start in service mode")
    p.add_argument('--service-interval', help='set run interval [in minutes, default %(default)s]',
                   default=SERVICE_INTERVAL)
    p.add_argument('--ignore-unknown', action='store_true')

    p.add_argument('--config', help='specify csirtg-smrt config path [default %(default)s', default=CONFIG_PATH)

    p.add_argument('--user')

    p.add_argument('--delay', help='specify initial delay', default=randint(5, 55))

    p.add_argument('--remember-path', help='specify remember db path [default: %(default)s', default=ARCHIVE_PATH)
    p.add_argument('--remember', help='remember what has been already processed', action='store_true')

    p.add_argument('--format', help='specify output format [default: %(default)s]"', default=FORMAT,
                   choices=FORMATS.keys())

    p.add_argument('--filter-indicator', help='filter for specific indicator, useful in testing')

    p.add_argument('--fireball', help='run in fireball mode, bulk+async magic', action='store_true')
    p.add_argument('--no-fetch', help='do not re-fetch if the cache exists', action='store_true')

    p.add_argument('--no-verify-ssl', help='turn TLS/SSL verification OFF', action='store_true')

    p.add_argument('--goback', help='specify default number of days to start out at [default %(default)s]',
                   default=GOBACK_DAYS)

    p.add_argument('--fields', help='specify fields for stdout [default %(default)s]"', default=','.join(STDOUT_FIELDS))

    p.add_argument('--skip-invalid', help="skip invalid indicators in DEBUG (-d) mode", action="store_true")
    p.add_argument('--skip-broken', help='skip seemingly broken feeds', action='store_true')

    p.add_argument('--send-retries', help='specify how many times to re-try sending indicators after a failure '
                                          '[default: %(default)s', default=5)
    p.add_argument('--send-retries-wait', help='how many seconds to wait between retries [default: %(default)s',
                   default=30)

    args = p.parse_args()

    o = read_config(args)
    options = vars(args)
    for v in options:
        if options[v] is None:
            options[v] = o.get(v)

    setup_logging(args)
    logger.info('loglevel is: {}'.format(logging.getLevelName(logger.getEffectiveLevel())))

    setup_runtime_path(args.runtime_path)

    verify_ssl = True
    if options.get('no_verify_ssl') or o.get('no_verify_ssl'):
        verify_ssl = False

    goback = args.goback
    if goback:
        goback = arrow.utcnow().replace(days=-int(goback))

    if not args.service:
        data = None
        if select.select([sys.stdin, ], [], [], 0.0)[0]:
            data = sys.stdin.read()

        try:
            _run_smrt(options, **{
                'args': args,
                'data': data,
                'verify_ssl': verify_ssl,
                'goback': goback
            })
        except KeyboardInterrupt:
            logger.info('exiting..')

        raise SystemExit

    # we're running as a service
    setup_signals(__name__)
    service_interval = int(args.service_interval)
    r = int(args.delay)
    logger.info("random delay is {}, then running every {} min after that".format(r, service_interval))

    if r != 0:
        try:
            sleep((r * 60))

        except KeyboardInterrupt:
            logger.info('shutting down')
            raise SystemExit

        except Exception as e:
            logger.error(e)
            raise SystemExit

    logger.info('starting...')

    def _run():
        logger.debug('forking process...')
        p = Process(target=_run_smrt, args=(options,), kwargs={
            'args': args,
            'verify_ssl': verify_ssl,
            'goback': goback,
            'service_mode': True
        })

        p.daemon = False
        p.start()
        p.join()
        logger.debug('child process re-joined')

    # first run, PeriodicCallback has builtin wait..
    _run()

    main_loop = ioloop.IOLoop()
    service_interval = (service_interval * 60000)
    loop = ioloop.PeriodicCallback(_run, service_interval)

    try:
        loop.start()
        main_loop.start()

    except KeyboardInterrupt:
        logger.info('exiting..')
        pass

    except Exception as e:
        logger.error(e)
        pass

if __name__ == "__main__":
    main()
