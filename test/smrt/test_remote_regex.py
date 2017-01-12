import py.test

from csirtg_smrt import Smrt
from pprint import pprint


def test_smrt_remote_regex():
    with Smrt(None, None, client='dummy') as s:
        assert type(s) is Smrt

        x = []
        for r, f in s.load_feeds('test/smrt/remote_regex.yml', feed='port-scanners'):
            x = list(s.process(r, f))
            assert len(x) > 0

        x = []
        for r, f in s.load_feeds('test/smrt/remote_regex.yml', feed='port-scanners-fail'):
            try:
                x = list(s.process(r, f))
            except RuntimeError as e:
                pass

            assert len(x) == 0

