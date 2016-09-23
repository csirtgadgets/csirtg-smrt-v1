import copy
import json
from csirtg_smrt.parser import Parser
from csirtg_indicator.utils import normalize_itype
from csirtg_indicator import Indicator
BATCH_SIZE = 500

class Json(Parser):

    def __init__(self, *args, **kwargs):
        super(Json, self).__init__(*args, **kwargs)

    def process(self):
        defaults = self._defaults()
        map = self.rule.feeds[self.feed]['map']
        values = self.rule.feeds[self.feed]['values']

        rv = []
        batch = []
        for l in self.fetcher.process():
            i = copy.deepcopy(defaults)

            l = json.loads(l)
            for e in l:
                i = {}
                for x, c in enumerate(map):
                    i[values[x]] = e[c]

                try:
                    self.logger.debug(i)
                    i = normalize_itype(i)
                    i = Indicator(**i)
                except NotImplementedError as e:
                    self.logger.error(e)
                    self.logger.info('skipping: {}'.format(i['indicator']))
                else:
                    if self.is_archived(i.indicator, i.provider, i.group, i.tags, i.firsttime, i.lasttime):
                        self.logger.info('skipping: {}/{}'.format(i.provider, i.indicator))
                    else:
                        if self.fireball:
                            batch.append(i)

                            if len(batch) == BATCH_SIZE:
                                r = self.client.indicators_create(batch)
                                for i in batch:
                                    rv.append(i)
                        else:
                            r = self.client.indicators_create(i)
                            self.archive(i.indicator, i.provider, i.group, i.tags, i.firsttime, i.lasttime)
                            rv.append(r)

                        if self.limit:
                            self.limit -= 1

                            if self.limit == 0:
                                self.logger.debug('limit reached...')
                                break

        if self.fireball and len(batch):
            r = self.client.indicators_create(batch)
            if len(r) == len(batch):
                for i in batch:
                    rv.append(i)
                    self.archive(i.indicator, i.provider, i.group, i.tags, i.firsttime, i.lasttime)
                else:
                    raise RuntimeError(r)

        return rv

Plugin = Json