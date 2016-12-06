import py.test

from csirtg_smrt import Smrt
from csirtg_smrt.rule import Rule
from csirtg_smrt.constants import REMOTE_ADDR
from csirtg_smrt.exceptions import RuleUnsupported
from pprint import pprint


def test_smrt_base():
    with Smrt(REMOTE_ADDR, 1234, client='dummy') as s:
        assert type(s) is Smrt

        for r, f in s.load_feeds('test/smrt/rules'):
            x = list(s.process(r, f))
            assert len(x) > 0

        x = []
        for r, f in s.load_feeds('test/smrt/rules/csirtg.yml'):
            x = list(s.process(r, f))
            assert len(x) > 0

        x = []
        for r, f in s.load_feeds('test/smrt/rules/csirtg.yml', feed='port-scanners'):
            x = list(s.process(r, f))
            assert len(x) > 0

        x = []
        try:
            r, f = next(s.load_feeds('test/smrt/rules/csirtg.yml', feed='port-scanners2'))
        except KeyError:
            pass

        assert len(x) == 0


def test_smrt_rule_paths():
    with Smrt(REMOTE_ADDR, 1234, client='dummy') as s:

        r, f = next(s.load_feeds('test/smrt/rules/csirtg.yml', feed='port-scanners'))
        assert f is not None
        assert r is not None

        r, f = (None, None)

        try:
            r, f = next(s.load_feeds('test/smrt/rules/csirtg.yml~', feed='port-scanners'))
        except RuleUnsupported:
            pass

        assert f is None