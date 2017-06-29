import copy

from stix.core import STIXPackage
from pprint import pprint
from csirtg_smrt.parser import Parser
from csirtg_indicator.utils import resolve_itype


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
        header = d['stix_header']

        for e in d.get('indicators'):
            if not e['observable']:
                continue

            i = copy.deepcopy(defaults)
            i['description'] = e['title'].lower()
            i['lasttime'] = e.get('timestamp')
            try:
                i['indicator'] = e['observable']['object']['properties']['value']['value']
            except KeyError:
                if e['observable']['object']['properties'].get('address_value'):
                    i['indicator'] = e['observable']['object']['properties']['address_value']['value']

                if e['observable']['object']['properties'].get('hashes'):
                    i['indicator'] = e['observable']['object']['properties']['hashes'][0]['simple_hash_value']['value']

                if e['observable']['object']['properties'].get('header'):
                    i['indicator'] = e['observable']['object']['properties']['header']['from']['address_value']['value']

            try:
                i['tlp'] = header['handling'][0]['marking_structures'][1]['color'].lower()
            except KeyError:
                i['tlp'] = header['handling'][0]['marking_structures'][0]['color']

            i['indicator'] = i['indicator'].lower()
            i['tlp'] = i['tlp'].lower()

            if not i.get('indicator'):
                continue

            if self.itype:
                if resolve_itype(i['indicator']) != self.itype:
                    continue

            yield i

Plugin = Stix
