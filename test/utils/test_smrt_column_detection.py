from csirtg_smrt.utils.zcolumns import get_indicator
from faker import Faker
fake = Faker()
from datetime import datetime
from csirtg_indicator import Indicator
from pprint import pprint
from random import randint, shuffle, choice


def test_smrt_column_detection():
    tags = ['scanner', 'phishing', 'botnet', 'malware']
    for x in range(0, 25):
        indicators = [fake.ipv4(), fake.url(), fake.ipv6(), fake.domain_name(), fake.email()]
        for i in indicators:
            i1 = Indicator(i, firsttime=datetime.utcnow(), lasttime=datetime.utcnow(), portlist=randint(1, 65535),
                           tags=choice(tags), description=' '.join(fake.words()))

            cols = [i1.indicator, i1.lasttime, i1.portlist, i1.firsttime, i1.tags[0], i1.description]
            shuffle(cols)
            i2 = get_indicator(cols)
            i2.uuid = i1.uuid

            assert i1 == i2
