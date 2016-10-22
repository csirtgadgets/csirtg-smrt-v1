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

        rv = []

        for d in self.fetcher.process(split=False):

            body = parse_email_from_string(d)

            obs = {}
            for k, v in defaults.items():
                obs[k] = v

            if self.headers:
                for h in self.headers:
                    if body[0]['headers'].get(h):
                        obs[self.headers[h]] = body[0]['headers'][h][0]

            obs['message'] = d

            try:
                i = Indicator(**obs)
            except InvalidIndicator as e:
                self.logger.error(e)
                self.logger.info('skipping: {}'.format(obs['indicator']))
            else:
                if self.is_archived(i.indicator, i.provider, i.group, i.tags, i.firsttime, i.lasttime):
                    self.logger.info('skipping: {}/{}'.format(i.provider, i.indicator))
                else:
                    r = self.client.indicators_create(i)
                    self.archive(i.indicator, i.provider, i.group, i.tags, i.firsttime, i.lasttime)
                    rv.append(r)

                    if self.limit:
                        self.limit -= 1

                        if self.limit == 0:
                            self.logger.debug('limit reached...')
                            break

        return rv

Plugin = Email
