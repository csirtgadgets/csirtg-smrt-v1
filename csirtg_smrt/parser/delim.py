from csirtg_smrt.parser import Parser
import re
from pprint import pprint


class Delim(Parser):

    def __init__(self, *args, **kwargs):
        super(Delim, self).__init__(*args, **kwargs)

        self.pattern = re.compile("\s+")

        if self.rule.delim_pattern:
            self.pattern = re.compile(self.rule.delim_pattern)

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
                        try:
                            i[col] = m[idx]
                        except IndexError as e:
                            self.logger.error(l)
                            raise

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
