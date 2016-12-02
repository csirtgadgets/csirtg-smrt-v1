import py.test

from csirtg_smrt import Smrt
from csirtg_smrt.rule import Rule
from csirtg_smrt.constants import REMOTE_ADDR
from pprint import pprint

rule = 'test/spamhaus/spamhaus.yml'
rule = Rule(path=rule)
rule.fetcher = 'file'
s = Smrt(REMOTE_ADDR, 1234, client='dummy')


def test_spamhaus_drop():
    rule.feeds['drop']['remote'] = 'test/spamhaus/drop.txt'
    x = s.process(rule, feed="drop")
    x = list(x)
    assert len(list(x)) > 0


def test_spamhaus_edrop():
    rule.feeds['edrop']['remote'] = 'test/spamhaus/edrop.txt'
    x = s.process(rule, feed="edrop")
    x = list(x)
    assert len(x) > 0
