import py.test

from csirtg_smrt import Smrt
from pprint import pprint


def test_smrt():
    with Smrt(remote='localhost:514', client='syslog') as s:
        assert type(s) is Smrt

        pprint(s)

        x = s.process('test/smrt/rules/csirtg.yml', feed='port-scanners')
        assert len(x) > 0
