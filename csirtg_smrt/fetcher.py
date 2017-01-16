import logging
import subprocess
import os
from pprint import pprint

from csirtg_smrt.constants import VERSION, SMRT_CACHE, PYVERSION

import magic
import re
import sys
from time import sleep

RE_SUPPORTED_DECODE = re.compile("zip|lzf|lzma|xz|lzop")
RE_CACHE_TYPES = re.compile('([\w.-]+\.(csv|zip|txt|gz))$')

FETCHER_TIMEOUT = os.environ.get('CSIRTG_SMRT_FETCHER_TIMEOUT', 120)


class Fetcher(object):

    def __init__(self, rule, feed, cache=SMRT_CACHE, data=None, no_fetch=False):

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

        if self.rule.remote:
            self.remote = self.rule.remote
        elif self.rule.defaults and self.rule.defaults.get('remote'):
            self.remote = self.rule.defaults.get('remote')
        else:
            self.remote = self.rule.feeds[feed]['remote']

        if self.rule.remote_pattern:
            self.remote_pattern = self.rule.remote_pattern
        elif self.rule.defaults.get('remote_pattern'):
            self.remote_pattern = self.rule.defaults.get('remote_pattern')
        elif self.rule.feeds[feed].get('remote_pattern'):
            self.remote_pattern = self.rule.feeds[feed]['remote_pattern']

        if self.rule.token:
            header = 'Authorization: Token token='
            if self.rule.token_header:
                header = self.rule.token_header

            self.token = '{}{}'.format(header, self.rule.token)

        if self.rule.username:
            self.username = self.rule.username
            self.password = self.rule.password

        if self.rule.feeds[feed].get('filters'):
            self.filters = self.rule.feeds[feed]['filters']

        if not data:
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
            elif RE_CACHE_TYPES.search(self.remote):
                self.cache = RE_CACHE_TYPES.search(self.remote).groups()
                self.cache = os.path.join(self.dir, self.cache[0])
                self.cache_file = True
            else:
                self.cache = os.path.join(self.dir, self.feed)

            self.logger.debug('CACHE %s' % self.cache)

            self.ua = "User-Agent: csirtg-smrt/{0} (csirtgadgets.org)".format(VERSION)

            if not self.fetcher:
                if self.remote.startswith('http'):
                    self.fetcher = 'http'
                else:
                    self.fetcher = 'file'

    def process(self, split="\n", limit=0, rstrip=True):
        if self.data:
            if isinstance(self.data, str):
                if split:
                    for l in self.data.split(split):
                        if rstrip:
                            l = l.rstrip()

                        yield l
                else:
                    yield self.data
            else:
                for d in self.data:
                    yield d
        else:
            if self.fetcher == 'http':
                cmd = ['wget', '--header', self.ua]

                if self.username:
                    cmd.extend(['--user', self.username, '--password', self.password])

                elif self.token:
                    cmd.extend(['--header', self.token])
                    cmd.extend(['--header', 'Accept: application/json'])

                cmd.extend(['--timeout={}'.format(self.fetcher_timeout)])

                if not self.logger.getEffectiveLevel() == logging.DEBUG:
                    cmd.append('-q')

                if self.filters:
                    filters = ['{}={}'.format(f, self.filters[f]) for f in self.filters]

                    self.remote = '{}?{}'.format(self.remote, '&'.join(filters))

                cmd.extend([self.remote, '-N'])

                if self.cache_file:
                    cmd.append('-P')
                    cmd.append(self.dir)
                else:
                    cmd.append('-O')
                    cmd.append(self.cache)

                self.logger.debug(cmd)
                if self.no_fetch and os.path.isfile(self.cache):
                    self.logger.info('skipping fetch: {}'.format(self.cache))
                else:
                    failed = 0
                    while failed < 5:
                        if failed > 0:
                            self.logger.info('retrying in 5s')
                            sleep(5)

                        try:
                            subprocess.check_call(cmd)
                            failed = 0
                            break
                        except subprocess.CalledProcessError as e:
                            failed += 1
                            self.logger.error('failure pulling feed: {} to {}'.format(self.remote, self.dir))
                            if self.logger.getEffectiveLevel() == logging.DEBUG:
                                raise e
                            else:
                                self.logger.error(e)

                    if failed:
                        return
            else:
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

                else:
                    raise NotImplementedError

            ftype = magic.from_file(self.cache, mime=True)
            if PYVERSION < 3:
                ftype = ftype.decode('utf-8')

            self.logger.debug(ftype)

            if ftype.startswith('application/x-gzip') or ftype.startswith('application/gzip'):
                import gzip
                with gzip.open(self.cache, 'rb') as f:
                    for l in f:
                        if rstrip:
                            l = l.rstrip()

                        if PYVERSION > 2:
                            l = l.decode('utf-8')

                        yield l

            elif ftype.startswith('text') or ftype.startswith('application/xml'):
                with open(self.cache) as f:
                    for l in f:
                        if rstrip:
                            l = l.rstrip()

                        if PYVERSION > 2 and isinstance(l, bytes):
                            l = l.decode('utf-8')

                        yield l

            elif ftype == "application/zip":
                from zipfile import ZipFile
                with ZipFile(self.cache) as f:
                    for m in f.infolist():
                        if PYVERSION == 2:
                            for l in f.read(m.filename).split(split):
                                if rstrip:
                                    l = l.rstrip()

                                yield l
                        else:
                            with f.open(m.filename) as zip:
                                for l in zip.readlines():
                                    if rstrip:
                                        l = l.rstrip()

                                    try:
                                        l = l.decode()
                                    except UnicodeDecodeError as e:
                                        l = l.decode('latin-1')

                                    yield l

            elif self.cache.endswith('.txt') and ftype == 'application/octet-stream':
                with open(self.cache) as f:
                    for l in f:
                        if rstrip:
                            l = l.rstrip()

                        if PYVERSION > 2 and isinstance(l, bytes):
                            l = l.decode('utf-8')

                        yield l
