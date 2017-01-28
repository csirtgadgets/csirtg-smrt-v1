import pytest
from csirtg_smrt import Smrt
from pprint import pprint

ZYRE_TEST = False

try:
    import pyzyre
    ZYRE_TEST = True
except ImportError:
    pass


@pytest.mark.skipif(ZYRE_TEST is False, reason='pyzyre not installed')
def test_zyre():
    with Smrt(remote=None, client='zyre') as s:
        assert type(s) is Smrt

        x = s.process('test/smrt/rules/csirtg.yml', feed='port-scanners', limit=2)
        assert len(x) > 0
