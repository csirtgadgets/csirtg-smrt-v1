from csirtg_smrt.parser import Parser
from csirtg_indicator import Indicator
from csirtg_indicator.exceptions import InvalidIndicator
from csirtg_indicator.utils import normalize_itype
from pprint import pprint


class Delim(Parser):

    def __init__(self, *args, **kwargs):
        super(Delim, self).__init__(*args, **kwargs)

    def process(self):
        defaults = self._defaults()
        cols = defaults.get('values', [])

        for l in self.fetcher.process():
            if self.ignore(l):  # comment or skip
                continue

            l = l.replace('\"', '')
            m = self.pattern.split(l)

            if len(cols):
                i = {}
                for k, v in defaults.items():
                    i[k] = v

                for idx, col in enumerate(cols):
                    if col is not None:
                        i[col] = m[idx]
                i.pop("values", None)
                self.eval_obs(i)

                skip = True
                if self.filters and self.filters.keys():
                    for f in self.filters:
                        if i.get(f) and i[f] == self.filters[f]:
                            skip = False
                else:
                    skip = False

                if skip:
                    self.logger.debug('skipping %s' % i['indicator'])
                    continue

                yield i

            if self.limit:
                self.limit -= 1

            if self.limit == 0:
                self.logger.debug('limit reached...')
                break

Plugin = Delim
