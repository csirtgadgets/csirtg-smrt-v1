import py.test

from csirtg_smrt import Smrt
from pprint import pprint


def test_smrt_csv_quoted():
    with Smrt(None, None, client='dummy') as s:
        assert type(s) is Smrt

        x = []
        for r, f in s.load_feeds('test/smrt/rules/csv_quoted.yml', feed='test'):
            x = list(s.process(r, f))
            assert len(x) > 0