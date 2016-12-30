import py.test

from csirtg_smrt import Smrt
from csirtg_smrt.rule import Rule
from csirtg_smrt.constants import REMOTE_ADDR
from pprint import pprint

rule = 'test/sansedu/sans_edu.yml'
rule = Rule(path=rule)
rule.fetcher = 'file'
s = Smrt(REMOTE_ADDR, 1234, client='dummy')


def test_sans_low():
    feed = '02_domains_low'
    x = s.process(rule, feed=feed)
    x = list(x)

    assert len(x) > 0

    assert len(x[0].indicator) > 4


def test_sans_block():
    feed = 'block'
    x = s.process(rule, feed=feed)
    x = list(x)

    assert len(x) > 0
    assert len(x[0].indicator) > 4
