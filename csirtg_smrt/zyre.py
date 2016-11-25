#!/usr/bin/env python

import logging
import os.path
import textwrap
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from random import randint
from time import sleep
from pprint import pprint
import traceback
import sys
import select

import csirtg_smrt.parser
from csirtg_smrt.archiver import Archiver
import csirtg_smrt.client
from csirtg_smrt.constants import REMOTE_ADDR, SMRT_RULES_PATH, SMRT_CACHE, CONFIG_PATH, RUNTIME_PATH, VERSION
from csirtg_smrt.rule import Rule
from csirtg_smrt.fetcher import Fetcher
from csirtg_smrt.utils import setup_logging, get_argument_parser, load_plugin, setup_signals, read_config, \
    setup_runtime_path
from csirtg_smrt.exceptions import AuthError, TimeoutError
from csirtg_indicator.format import FORMATS

PARSER_DEFAULT = "pattern"
TOKEN = os.environ.get('CSIRTG_TOKEN', None)
TOKEN = os.environ.get('CSIRTG_SMRT_TOKEN', TOKEN)
ARCHIVE_PATH = os.environ.get('CSIRTG_SMRT_ARCHIVE_PATH', RUNTIME_PATH)
ARCHIVE_PATH = os.path.join(ARCHIVE_PATH, 'smrt_zyre.db')
FORMAT = os.environ.get('CSIRTG_SMRT_FORMAT', 'table')

# http://python-3-patterns-idioms-test.readthedocs.org/en/latest/Factory.html
# https://gist.github.com/pazdera/1099559
logging.getLogger("requests").setLevel(logging.WARNING)


class Zyre(object):

    def __init__(self, token=TOKEN, remote=REMOTE_ADDR, client='stdout', username=None, feed=None, archiver=None,
                 fireball=False, no_fetch=False):

        self.logger = logging.getLogger(__name__)

        plugin_path = os.path.join(os.path.dirname(__file__), 'client')
        if getattr(sys, 'frozen', False):
            plugin_path = os.path.join(sys._MEIPASS, 'csirtg_smrt', 'client')

        self.client = load_plugin(plugin_path, client)

        if not self.client:
            raise RuntimeError("Unable to load plugin: {}".format(client))

        self.client = self.client(remote=remote, token=token, username=username, feed=feed, fireball=fireball)

        self.archiver = archiver
        self.fireball = fireball
        self.no_fetch = no_fetch

    def ping_remote(self):
        return self.client.ping(write=True)

    def _process(self, rule, feed, limit=None, data=None, filters=None):
        fetch = Fetcher(rule, feed, data=data, no_fetch=self.no_fetch)

        parser_name = rule.parser or PARSER_DEFAULT
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

        parser = parser(self.client, fetch, rule, feed, limit=limit, archiver=self.archiver, filters=filters,
                        fireball=self.fireball)

        rv = parser.process()

        return rv

    def process(self, rule, data=None, feed=None, limit=None, filters=None):
        rv = []
        if isinstance(rule, str) and os.path.isdir(rule):
            for f in os.listdir(rule):
                if not f.startswith('.'):
                    self.logger.debug("processing {0}/{1}".format(rule, f))
                    r = Rule(path=os.path.join(rule, f))

                    if not r.feeds:
                        continue

                    for feed in r.feeds:
                        try:
                            rv = self._process(r, feed, limit=limit, filters=filters)
                        except Exception as e:
                            self.logger.error('failed to process: {}'.format(feed))
                            self.logger.error(e)
                            traceback.print_exc()

        else:
            self.logger.debug("processing {0}".format(rule))
            r = rule
            if isinstance(rule, str):
                r = Rule(path=rule)

            if not r.feeds:
                self.logger.error("rules file contains no feeds")
                raise RuntimeError

            if feed:
                try:
                    rv = self._process(r, feed, limit=limit, data=data, filters=filters)
                except Exception as e:
                    self.logger.error('failed to process feed: {}'.format(feed))
                    self.logger.error(e)
                    traceback.print_exc()
            else:
                for feed in r.feeds:
                    try:
                        rv = self._process(Rule(path=rule), feed=feed, limit=limit, data=data, filters=filters)
                    except Exception as e:
                        self.logger.error('failed to process feed: {}'.format(feed))
                        self.logger.error(e)
                        traceback.print_exc()

        return rv


def main():
    p = get_argument_parser()
    p = ArgumentParser(
        description=textwrap.dedent('''\
        Env Variables:
            CSIRTG_RUNTIME_PATH
            CSIRTG_TOKEN

        example usage:
            $ csirtg-smrt --rule rules/default
            $ csirtg-smrt --rule default/csirtg.yml --feed port-scanners --remote http://localhost:5000
        '''),
        formatter_class=RawDescriptionHelpFormatter,
        prog='csirtg-smrt',
        parents=[p],
    )

    p.add_argument("--remote", help="specify the remote api url")
    p.add_argument('--remote-type', help="specify remote type [cif, csirtg, elasticsearch, syslog, etc]")

    p.add_argument("--token", help="specify token [default: %(default)s]", default=TOKEN)

    p.add_argument('--channel', default='CSIRTG')

    args = p.parse_args()

    setup_logging(args)
    logger = logging.getLogger()
    logger.info('loglevel is: {}'.format(logging.getLevelName(logger.getEffectiveLevel())))

    s = Smrt(args.get('token'), args.get('remote'), client=args.client, username=args.user)


if __name__ == "__main__":
    main()
