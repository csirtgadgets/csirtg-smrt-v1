import logging
import subprocess
import os
from pprint import pprint
from csirtg_smrt.constants import VERSION, SMRT_CACHE, PYVERSION
from datetime import datetime
import magic
import re
import sys
from time import sleep
import arrow
import requests
logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.DEBUG)

RE_SUPPORTED_DECODE = re.compile("zip|lzf|lzma|xz|lzop")
RE_CACHE_TYPES = re.compile('([\w.-]+\.(csv|zip|txt|gz))$')

FETCHER_TIMEOUT = os.getenv('CSIRTG_SMRT_FETCHER_TIMEOUT', 120)
RETRIES = os.getenv('CSIRTG_SMRT_FETCHER_RETRIES', 3)
RETRIES_DELAY = os.getenv('CSIRTG_SMRT_FETCHER_RETRY_DELAY', 30) # seconds
NO_HEAD = os.getenv('CSIRTG_SMRT_FETCHER_NOHEAD')
logger = logging.getLogger(__name__)


class Fetcher(object):

    def __init__(self, rule, feed, cache=SMRT_CACHE, data=None, no_fetch=False, verify_ssl=True, limit=None):

        self.logger = logging.getLogger(__name__)
        self.feed = feed
        self.rule = rule
        self.cache = cache
        self.fetcher = rule.fetcher
        self.data = data
        self.cache_file = False
        self.no_fetch = no_fetch
        self.fetcher_timeout = FETCHER_TIMEOUT
        self.remote_pattern = None
        self.token = None
        self.username = None
        self.filters = None
        self.verify_ssl = verify_ssl
        self.limit = limit

        if self.rule.remote:
            self.remote = self.rule.remote
        elif self.rule.defaults and self.rule.defaults.get('remote'):
            self.remote = self.rule.defaults.get('remote')
        else:
            self.remote = self.rule.feeds[feed].get('remote')

        if self.rule.remote_pattern:
            self.remote_pattern = self.rule.remote_pattern
        elif self.rule.defaults.get('remote_pattern'):
            self.remote_pattern = self.rule.defaults.get('remote_pattern')
        elif self.rule.feeds[feed].get('remote_pattern'):
            self.remote_pattern = self.rule.feeds[feed]['remote_pattern']

        if self.remote and '{token}' in self.remote:
            if self.rule.token:
                self.remote = self.remote.format(token=self.rule.token)
            else:
                self.remote = self.remote.format(token='')

        elif self.rule.token:
            header = 'Authorization: Token token='
            if self.rule.token_header:
                header = self.rule.token_header

            self.token = '{}{}'.format(header, self.rule.token)

        if self.rule.username:
            self.username = self.rule.username
            self.password = self.rule.password

        if self.rule.feeds[feed].get('filters'):
            self.filters = self.rule.feeds[feed]['filters']

        if not self.filters:
            self.filters = {}

        if self.rule.limit:
            self.filters['limit'] = self.rule.limit

        if self.limit:
            self.filters['limit'] = self.limit

        if data:
            return

        self.dir = os.path.join(self.cache, self.rule.defaults.get('provider'))
        self.logger.debug(self.dir)

        if not os.path.exists(self.dir):
            try:
                os.makedirs(self.dir)
            except OSError:
                self.logger.critical('failed to create {0}'.format(self.dir))
                raise

        if self.rule.feeds[feed].get('cache'):
            self.cache = os.path.join(self.dir, self.rule.feeds[feed]['cache'])
            self.cache_file = True

        elif self.remote and RE_CACHE_TYPES.search(self.remote):
            self.cache = RE_CACHE_TYPES.search(self.remote).groups()
            self.cache = os.path.join(self.dir, self.cache[0])
            self.cache_file = True

        else:
            self.cache = os.path.join(self.dir, self.feed)

        self.logger.debug('CACHE %s' % self.cache)

        self.ua = "csirtg-smrt/{0} (csirtgadgets.org)".format(VERSION)

        if self.fetcher:
            return

        if self.remote.startswith('http'):
            self.fetcher = 'http'
        else:
            self.fetcher = 'file'

    def _process_data(self, split="\n", rstrip=True):
        if not isinstance(self.data, str):
            for d in self.data:
                yield d

            return

        if not split:
            yield self.data
            return

        for l in self.data.split(split):
            if rstrip:
                l = l.rstrip()

            yield l

    def _process_cache(self, split="\n", rstrip=True):
        try:
            ftype = magic.from_file(self.cache, mime=True)
        except AttributeError:
            try:
                mag = magic.open(magic.MAGIC_MIME)
                mag.load()
                ftype = mag.file(self.cache)
            except AttributeError as e:
                raise RuntimeError('unable to detect cached file type')
        
        if PYVERSION < 3:
            ftype = ftype.decode('utf-8')

        if ftype.startswith('application/x-gzip') or ftype.startswith('application/gzip'):
            from csirtg_smrt.decoders.zgzip import get_lines
            for l in get_lines(self.cache, split=split):
                yield l

            return

        if ftype == "application/zip":
            from csirtg_smrt.decoders.zzip import get_lines
            for l in get_lines(self.cache, split=split):
                yield l

            return

        # all others, mostly txt, etc...
        with open(self.cache) as f:
            for l in f:
                yield l

    def _cache_modified(self):
        ts = os.stat(self.cache)
        ts = arrow.get(ts.st_mtime)
        return ts

    def _cache_size(self):
        if not os.path.isfile(self.cache):
            return 0

        s = os.stat(self.cache)
        return s.st_size

    def _cache_refresh(self, s, auth):
        resp = s.get(self.remote, stream=True, auth=auth, timeout=self.fetcher_timeout, verify=self.verify_ssl)

        if resp.status_code == 200:
            return resp

        if resp.status_code == 429 or resp.status_code in [500, 502, 503, 504]:
            n = RETRIES
            retry_delay = RETRIES_DELAY
            while n != 0:
                if resp.status_code == 429:
                    logger.info('Rate Limit Exceeded, retrying in %ss' % retry_delay)
                else:
                    logger.error('%s found, retrying in %ss' % (resp.status_code, retry_delay))
                
                sleep(retry_delay)
                resp = s.get(self.remote, stream=True, auth=auth, timeout=self.fetcher_timeout,
                             verify=self.verify_ssl)
                if resp.status_code == 200:
                    return resp

                n -= 1

    def _cache_write(self, s):
        with open(self.cache, 'wb') as f:
            auth = False
            if self.username:
                auth = (self.username, self.password)

            resp = self._cache_refresh(s, auth)
            if not resp:
                return

            for block in resp.iter_content(1024):
                f.write(block)

    def _fetch(self):

        if self.filters:
            filters = ['{}={}'.format(f, self.filters[f]) for f in self.filters]
            self.remote = '{}?{}'.format(self.remote, '&'.join(filters))

        s = requests.session()

        s.headers['User-Agent'] = self.ua

        if self.token:
            t1, t2 = self.token.split(': ')
            s.headers[t1] = t2
            s.headers['Accept'] = 'application/json'

        if self._cache_size() == 0:
            logger.debug('cache size is 0, downloading...')
            self._cache_write(s)
            return

        logger.debug('checking HEAD')

        logger.debug('verify_ssl: {}'.format(self.verify_ssl))
        resp = s.head(self.remote, verify=self.verify_ssl)

        if not resp.headers.get('Last-Modified'):
            logger.debug('no last-modified header')
            self._cache_write(s)
            return

        ts = resp.headers.get('Last-Modified')

        ts1 = arrow.get(datetime.strptime(ts, '%a, %d %b %Y %X %Z'))
        ts2 = self._cache_modified()

        if not NO_HEAD and (ts1 <= ts2):
           logger.debug('cache is OK: {} <= {}'.format(ts1, ts2))
           return

        logger.debug("refreshing cache...")
        self._cache_write(s)

    def process(self, split="\n", rstrip=True):
        if self.data:
            for d in self._process_data(split=split, rstrip=rstrip):
                yield d

            return

        if self.fetcher == 'apwg' and os.environ.get('APWG_TOKEN'):
            from apwgsdk.client import Client as apwgcli
            cli = apwgcli()
            yield cli.indicators(no_last_run=True)
            return

        if self.fetcher == 'http':
            if self.no_fetch and os.path.isfile(self.cache):
                self.logger.info('skipping fetch: {}'.format(self.cache))
            else:
                try:
                    self._fetch()
                except Exception as e:
                    logger.error(e)

            # testing only, we need to re-write for smrtv1
            # fetcher loads the parsers, not the other way around
            from csirtg_smrt.utils.zcontent import get_type
            try:
                parser_name = get_type(self.cache)
                logger.debug(parser_name)
            except Exception as e:
                logger.debug(e)

            for l in self._process_cache(split=split, rstrip=rstrip):
                if rstrip:
                    l = l.rstrip()

                if PYVERSION > 2 and isinstance(l, bytes):
                    try:
                        l = l.decode('utf-8')
                    except Exception:
                        try:
                            l = l.decode('latin-1')
                        except Exception:
                            logger.error('unable to decode %s' % l)
                            continue

                yield l

            return

        if self.fetcher == 'file':
            self.cache = self.remote
            if self.remote_pattern:
                found = False
                for f in os.listdir(self.cache):
                    if re.match(self.remote_pattern, f):
                        self.cache = os.path.join(self.cache, f)
                        found = True

                if not found:
                    raise RuntimeError('unable to match file')

            for l in self._process_cache(split=split, rstrip=rstrip):
                if rstrip:
                    l = l.rstrip()

                if PYVERSION > 2 and isinstance(l, bytes):
                    try:
                        l = l.decode('utf-8')
                    except UnicodeDecodeError:
                        l = l.decode('latin-1')

                yield l
