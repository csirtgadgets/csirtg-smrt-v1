from csirtg_mail import from_string
from csirtg_smrt.parser import Parser
import logging
import os
import re
from pprint import pprint

TOKEN = os.environ.get('CSIRTG_TOKEN', None)
CSIRTG_SMRT_PREDICT = False
RE_PREDICT = re.compile(os.getenv('CSIRTG_PREDICT_RE', '^https?'))
if os.getenv('CSIRTG_SMRT_PREDICT') == '1':
    CSIRTG_SMRT_PREDICT = True

try:
    from csirtgsdk.client import Client as csirtg_client
    from csirtgsdk.predict import Predict
except Exception:
    pass

logger = logging.getLogger(__name__)


def _check_predict(i):
    c = csirtg_client(token=TOKEN)
    try:
        return Predict(c).get(i)
    except NameError:
        logger.error('missing newer version of csirtgsdk-py')
        logger.error('run `pip install csirtgsdk --upgrade` and try again')
        raise SystemExit


class Email(Parser):

    def __init__(self, *args, **kwargs):
        super(Email, self).__init__(*args, **kwargs)

        self.start_after = None

        if self.rule.feeds[self.feed].get('start_after'):
            self.start_after = self.rule.feeds[self.feed]['start_after']

        self.keep_msg = None
        if self.rule.feeds[self.feed].get('keep_msg'):
            self.keep_msg = self.rule.feeds[self.feed]['keep_msg']

        self.headers = None
        if self.rule.feeds[self.feed].get('headers'):
            self.headers = self.rule.feeds[self.feed]['headers']

    def process(self, data=None):
        defaults = self._defaults()

        for d in self.fetcher.process(split=False):

            body = from_string(d)

            # if we're pulling intel from headers (eg: spamcop)

            if 'indicator' in self.headers.values():
                i = {}
                for k, v in defaults.items():
                    i[k] = v

                for h in self.headers:
                    if body['headers'].get(h):
                        i[self.headers[h]] = body['headers'][h][0]

                i['message'] = d
                yield i
                continue

            # if we're pulling from a suspicious message
            _indicators = body['urls']
            _indicators.extend(body['email_addresses'])

            for _i in _indicators:
                i = {}
                for k, v in defaults.items():
                    i[k] = v

                if self.headers:
                    for h in self.headers:
                        if body['headers'].get(h):
                            i[self.headers[h]] = body['headers'][h][0]

                i['message'] = d
                i['indicator'] = _i

                if not CSIRTG_SMRT_PREDICT:
                    yield i
                    continue

                if not RE_PREDICT.match(i['indicator']):
                    yield i

                if _check_predict(i['indicator']):
                    yield i

Plugin = Email
