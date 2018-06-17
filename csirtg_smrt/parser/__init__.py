import logging
import re
import math
from ..constants import PYVERSION, FIREBALL_SIZE

RE_COMMENTS = '^([#|;]+)'


class Parser(object):

    def __init__(self, client, fetcher, rule, feed, limit=None, filters=None, fireball=False):

        self.logger = logging.getLogger(__name__)
        self.client = client
        self.fetcher = fetcher
        self.rule = rule
        self.feed = feed
        self.limit = limit
        self.skip = None
        self.filters = filters
        self.skip_first = False
        self.itype = None
        self.line_filter = None
        self.add_orig = False

        if fireball:
            self.fireball = int(FIREBALL_SIZE)
        else:
            self.fireball = False

        if self.limit is not None:
            self.limit = int(limit)

        self.comments = re.compile(RE_COMMENTS)

        if self.rule.feeds[self.feed].get('skip'):
            self.skip = re.compile(self.rule.feeds[self.feed]['skip'])
        elif self.rule.skip:
            self.skip = re.compile(self.rule.skip)

        if self.rule.feeds[self.feed].get('skip_first'):
            self.skip_first = True
        elif self.rule.skip_first:
            self.skip_first = True

        if self.rule.feeds[self.feed].get('itype'):
            self.itype = self.rule.feeds[self.feed]['itype']
        elif self.rule.itype:
            self.itype = self.rule.itype

        if self.rule.feeds[self.feed].get('line_filter'):
            self.line_filter = self.rule.feeds[self.feed]['line_filter']
        elif self.rule.line_filter:
            self.line_filter = self.rule.line_filter

        if self.line_filter:
            self.line_filter = re.compile(self.line_filter)

        self.line_count = 0

    def ignore(self, line):
        if line == '':
            return True

        if self.is_comment(line):
            return True

        self.line_count += 1
        if self.line_count == 1 and self.skip_first:
            return True

        if self.skip:
            if self.skip.search(line):
                return True

        if self.line_filter:
            if not self.line_filter.search(line):
                return True

    def is_comment(self, line):
        if self.comments.search(line):
            return True

    def _defaults(self):
        defaults = self.rule.defaults

        if self.rule.feeds[self.feed].get('defaults'):
            for d in self.rule.feeds[self.feed].get('defaults'):
                defaults[d] = self.rule.feeds[self.feed]['defaults'][d]

        return defaults

    def eval_obs(self, obs, value=None):
        if value is None:
            value = obs

        if isinstance(value, dict):
            for k in list(value.keys()):
                value[k] = self.eval_obs(obs, value[k])
        elif isinstance(value, list):
            for i in range(len(value)):
                value[i] = self.eval_obs(obs, value[i])
        elif PYVERSION > 2 and isinstance(value, (str, bytes)):
            try:
                m = re.match('^eval\((.*)\)$', value.strip(), re.MULTILINE | re.DOTALL)
                if m:
                    value = eval(m.group(1),{"__builtins__":None, 'math': math, 'max': max, 'min': min, 'int': int, 'float': float, 'str': str, 'unicode': bytes},{'obs': obs})
            except Exception as e:
                self.logger.warn('Could not evaluate expression "{}", exception: {}'.format(value, e))
        elif PYVERSION == 2 and isinstance(value, (str, unicode)):
            try:
                m = re.match('^eval\((.*)\)$', value.strip(), re.MULTILINE | re.DOTALL)
                if m:
                    value = eval(m.group(1),{"__builtins__":None, 'math': math, 'max': max, 'min': min, 'int': int, 'float': float, 'str': str, 'unicode': unicode},{'obs': obs})
            except Exception as e:
                self.logger.warn('Could not evaluate expression "{}", exception: {}'.format(value, e))

        return value

    def process(self):
        raise NotImplementedError
