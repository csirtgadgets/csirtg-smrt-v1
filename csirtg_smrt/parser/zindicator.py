from csirtg_smrt.parser import Parser
from pprint import pprint


class _Indicator(Parser):
    def __init__(self, *args, **kwargs):
        super(_Indicator, self).__init__(*args, **kwargs)

    def process(self):
        defaults = self._defaults()

        for l in self.fetcher.process():
            for e in l:
                i = {}
                e = e.__dict__()
                for k, v in e.items():
                    i[k] = v

                for k, v in defaults.items():
                    i[k] = v

                yield i


Plugin = _Indicator
