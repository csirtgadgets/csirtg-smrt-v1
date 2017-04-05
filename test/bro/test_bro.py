from csirtg_smrt.parser.bro import BroTailer
from pprint import pprint


def test_bro():
    file = 'test/bro/bro.log'

    b = BroTailer(file)

    events = []
    with open(file) as f:
        for l in f.read().split("\n"):
            if l.startswith('#'):
                continue

            i = b.parse_line(l)

            if not i:
                continue

            events.append(i)

    assert len(events) > 0
    assert events[0]['indicator'] == '138.117.125.206'
