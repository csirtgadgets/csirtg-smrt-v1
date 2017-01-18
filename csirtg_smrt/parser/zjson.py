import copy
import json
from csirtg_smrt.parser import Parser
from csirtg_indicator import Indicator
from csirtg_indicator.utils import normalize_itype


class Json(Parser):

    def __init__(self, *args, **kwargs):
        super(Json, self).__init__(*args, **kwargs)

    def process(self):
        defaults = self._defaults()
        map = self.rule.feeds[self.feed].get('map')
        values = self.rule.feeds[self.feed].get('values')

        for l in self.fetcher.process():

            l = json.loads(l)
            for e in l:
                i = copy.deepcopy(defaults)

                if map:
                    for x, c in enumerate(map):
                        i[values[x]] = e[c]

                yield i

Plugin = Json
