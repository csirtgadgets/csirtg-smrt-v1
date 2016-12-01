from csirtg_smrt.parser import Parser
from csirtg_indicator import Indicator
from csirtg_indicator.exceptions import InvalidIndicator
from pprint import pprint


class Delim(Parser):

    def __init__(self, *args, **kwargs):
        super(Delim, self).__init__(*args, **kwargs)

    def process(self):
        defaults = self._defaults()
        cols = defaults['values']

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

                skip = True
                if self.filters and self.filters.keys():
                    for f in self.filters:
                        if obs.get(f) and obs[f] == self.filters[f]:
                            skip = False
                else:
                    skip = False

                if skip:
                    self.logger.info('skipping %s' % obs['indicator'])
                    continue

                try:
                    i = Indicator(**obs)
                    yield i.__dict__()
                except InvalidIndicator as e:
                    self.logger.error(e)
                    self.logger.info('skipping: {}'.format(obs['indicator']))

            if self.limit:
                self.limit -= 1

            if self.limit == 0:
                self.logger.debug('limit reached...')
                break

Plugin = Delim
