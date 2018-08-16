import json
from csirtg_smrt.parser import Parser
import os
import logging

TRACE = os.environ.get('CSIRTG_SMRT_PARSER_TRACE')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not TRACE:
    logger.setLevel(logging.ERROR)


class Cifv2(Parser):

    def __init__(self, *args, **kwargs):
        super(Cifv2, self).__init__(*args, **kwargs)

    def process(self):
        for l in self.fetcher.process():

            try:
                l = json.loads(l)
            except ValueError as e:
                logger.error('json parsing error: {}'.format(e))
                continue

            for e in l:
                e['indicator'] = e['observable']
                e['itype'] = e['otype']

                e['confidence'] = e['confidence'] / 10.0

                if isinstance(e['group'], list):
                    e['group'] = e['group'][0]
                
                yield e

Plugin = Cifv2
