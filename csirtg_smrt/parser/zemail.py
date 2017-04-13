from csirtg_mail import parse_email_from_string
from csirtg_smrt.parser import Parser
from csirtg_indicator import Indicator
from csirtg_indicator.exceptions import InvalidIndicator
from pprint import pprint
import logging

logger = logging.getLogger(__name__)


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

            body = parse_email_from_string(d)

            i = {}
            for k, v in defaults.items():
                i[k] = v

            if self.headers:
                for h in self.headers:
                    if body[0]['headers'].get(h):
                        i[self.headers[h]] = body[0]['headers'][h][0]

            i['message'] = d

            yield i

Plugin = Email
