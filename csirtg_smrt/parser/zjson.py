import copy
import json
from csirtg_smrt.parser import Parser
import logging
import os
from pprint import pprint

TRACE = os.environ.get('CSIRTG_SMRT_PARSER_TRACE')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not TRACE:
    logger.setLevel(logging.ERROR)


class Json(Parser):

    def __init__(self, *args, **kwargs):
        super(Json, self).__init__(*args, **kwargs)

    def process(self):
        defaults = self._defaults()
        map = self.rule.feeds[self.feed].get('map')
        values = self.rule.feeds[self.feed].get('values')
        envelope = self.rule.feeds[self.feed].get('envelope')

        for l in self.fetcher.process():
            try:
                l = json.loads(l)
            except ValueError as e:
                logger.error('json parsing error: {}'.format(e))
                continue

            if envelope:
                l = l[envelope]

            for e in l:
                i = copy.deepcopy(defaults)

                if map:
                    for x, c in enumerate(map):
                        i[values[x]] = e[c]

                yield i

Plugin = Json
