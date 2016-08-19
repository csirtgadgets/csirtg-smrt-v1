from csirtg_smrt.parser import Parser
from csirtg_indicator import Indicator
from csirtg_indicator.exceptions import InvalidIndicator


class Delim(Parser):

    def __init__(self, *args, **kwargs):
        super(Delim, self).__init__(*args, **kwargs)

    def process(self):
        defaults = self._defaults()
        cols = defaults['values']

        rv = []
        for l in self.fetcher.process():
            if l == '' or self.is_comment(l):
                continue

            l = l.replace('\"', '')
            m = self.pattern.split(l)

            if len(cols):
                obs = {}
                for k, v in defaults.items():
                    obs[k] = v

                for idx, col in enumerate(cols):
                    if col is not None:
                        obs[col] = m[idx]
                obs.pop("values", None)
                self.eval_obs(obs)

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

            if self.limit:
                self.limit -= 1

                if self.limit == 0:
                    self.logger.debug('limit reached...')
                    break

        return rv

Plugin = Delim