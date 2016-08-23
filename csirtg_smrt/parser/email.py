from cgmail import parse_email_from_string
from csirtg_smrt.parser import Parser
from csirtg_indicator import Indicator
from csirtg_indicator.exceptions import InvalidIndicator


class Email(Parser):

    def __init__(self, data=None, *args, **kwargs):
        super(Email, self).__init__(*args, **kwargs)

    def process(self, data=None):
        defaults = self._defaults()

        rv = []

        for d in data:
            d = parse_email_from_string(d)

            obs = {}
            for k, v in defaults.items():
                obs[k] = v

            obs['indicator'] = d[0]['headers']['X-SpamCop-sourceip']

            try:
                i = Indicator(**obs)
            except InvalidIndicator as e:
                self.logger.error(e)
                self.logger.info('skipping: {}'.format(obs['indicator']))
            else:
                self.logger.debug(obs)
                self.logger.debug(i)
                if self.is_archived(i.indicator, i.provider, i.group, i.tags, i.firsttime, i.lasttime):
                    self.logger.info('skipping: {}/{}'.format(i.provider, i.indicator))
                else:
                    r = self.client.indicators_create(i)
                    self.archive(i.indicator, i.provider, i.group, i.tags, i.firsttime, i.lasttime)
                    rv.append(r)

        return rv

Plugin = Email
