import copy
import re

from stix.core import STIXPackage
from pprint import pprint
from csirtg_smrt.parser import Parser


class Stix(Parser):

    def __init__(self, *args, **kwargs):
        super(Stix, self).__init__(*args, **kwargs)

    def process(self):
        defaults = self._defaults()

        try:
            feed = STIXPackage.from_xml(self.rule.remote)
        except Exception as e:
            self.logger.error('Error parsing feed: {}'.format(e))
            self.logger.error(defaults['remote'])
            raise e

        d = feed.to_dict()

        for e in d.get('indicators'):
            if not e['observable']:
                continue

            i = copy.deepcopy(defaults)
            i['description'] = e['title']
            i['lasttime'] = e['timestamp']
            i['indicator'] = e['observable']['object']['properties']['value']['value']

            if not i.get('indicator'):
                continue

            yield i

Plugin = Stix
