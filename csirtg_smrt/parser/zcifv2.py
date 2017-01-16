import copy
import json
from csirtg_smrt.parser import Parser


class Cifv2(Parser):

    def __init__(self, *args, **kwargs):
        super(Cifv2, self).__init__(*args, **kwargs)

    def process(self):
        for l in self.fetcher.process():

            l = json.loads(l)

            for e in l:
                e['indicator'] = e['observable']
                e['itype'] = e['otype']

                yield e

Plugin = Cifv2
