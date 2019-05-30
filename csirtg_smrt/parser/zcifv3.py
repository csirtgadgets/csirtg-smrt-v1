import copy
import json
from csirtg_smrt.parser import Parser
from cifsdk.constants import PYVERSION
import logging
import os
from pprint import pprint

if PYVERSION == 3:
    basestring = (str, bytes)

TRACE = os.environ.get('CSIRTG_SMRT_PARSER_TRACE')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not TRACE:
    logger.setLevel(logging.ERROR)


class cifv3(Parser):

    def __init__(self, *args, **kwargs):
        super(cifv3, self).__init__(*args, **kwargs)

    def process(self):
        defaults = self._defaults()
        values = self.rule.feeds[self.feed].get('values')
        envelope = self.rule.feeds[self.feed].get('envelope')

        for l in self.fetcher.process():
            try:
                l = json.loads(l)
            except ValueError as e:
                logger.error('json parsing error: {}'.format(e))
                continue

            if l.get('data') and isinstance(l['data'], basestring) and l['data'].startswith('{"hits":{"hits":[{"_source":'):
                l['data'] = json.loads(l['data'])
                l['data'] = [r['_source'] for r in l['data']['hits']['hits']]

            if envelope:
                l = l[envelope]

            if l.get('data') != '{}':
                for e in l['data']:
                    if isinstance(e['group'], list):
                        e['group'] = e['group'][0]

                    i = copy.deepcopy(defaults)

                    if values:
                        for value in values:
                            i[value] = e[value]
                    else:
                        for value in e.keys():
                            i[value] = e[value]
                    yield i
            else:
                return

Plugin = cifv3
