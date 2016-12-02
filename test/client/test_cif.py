import py.test

from csirtg_smrt import Smrt
from pprint import pprint


def test_smrt():
    with Smrt(remote='localhost:514', client='syslog') as s:
        assert type(s) is Smrt

        rule, feed = next(s.load_feeds('test/smrt/rules/csirtg.yml', 'port-scanners'))
        x = list(s.process(rule, feed))
        assert len(x) > 0
