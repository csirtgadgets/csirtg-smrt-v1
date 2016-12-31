import copy
import re

from csirtg_smrt.parser import Parser


class Pattern(Parser):

    def __init__(self, *args, **kwargs):
        super(Pattern, self).__init__(*args, **kwargs)

        self.pattern = self.rule.defaults.get('pattern')

        if self.rule.feeds[self.feed].get('pattern'):
            self.pattern = self.rule.feeds[self.feed].get('pattern')

        if self.pattern:
            self.pattern = re.compile(self.pattern)

        self.split = "\n"

        if self.rule.feeds[self.feed].get('values'):
            self.cols = self.rule.feeds[self.feed].get('values')
        else:
            self.cols = self.rule.defaults.get('values', [])

        self.defaults = self._defaults()

        if isinstance(self.cols, str):
            self.cols = self.cols.split(',')

    def process(self):
        for l in self.fetcher.process(split=self.split):

            if self.ignore(l):  # comment or skip
                continue

            self.logger.debug(l)

            try:
                m = self.pattern.search(l).groups()
                self.logger.debug(m)
                if isinstance(m, str):
                    m = [m]
            except ValueError as e:
                continue
            except AttributeError as e:
                continue

            i = copy.deepcopy(self.defaults)
            for idx, col in enumerate(self.cols):
                if col:
                    i[col] = m[idx]

            i.pop("values", None)
            i.pop("pattern", None)

            self.logger.debug(i)

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


Plugin = Pattern
