from csirtg_smrt.parser import Parser
import re
from pprint import pprint
import logging

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

            if (l.startswith('"') or l.startswith("'") and self.pattern == re.compile(',')) or (l.count(',') > 2):
                import csv
                r = csv.reader([l], delimiter=',', quotechar='"')
                m = next(r)
               # pprint(m)
            else:
                l = l.replace('\"', '')
                m = self.pattern.split(l)

            # l = l.replace('\"', '')
            # m = self.pattern.split(l)

            if len(cols):
                i = {}
                for k, v in defaults.items():
                    i[k] = v

                #pprint(i)
                for idx, col in enumerate(cols):
                    if col is not None:
                        try:
                            i[col] = m[idx]
                        except IndexError as e:
                            continue

                if self.add_orig:
                    i['additional_data'] = l

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
