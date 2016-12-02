import py.test

from csirtg_smrt import Smrt
from csirtg_smrt.rule import Rule
from csirtg_smrt.constants import REMOTE_ADDR
from pprint import pprint

rule = 'test/pastebin/pastebin.yml'
rule = Rule(path=rule)
rule.fetcher = 'file'

s = Smrt(REMOTE_ADDR, 1234, client='dummy')


def test_pastebin_creds():
    rule.feeds['creds']['remote'] = 'test/pastebin/feed.txt'
    x = s.process(rule, feed="creds")
    x = list(x)

    assert len(x) > 0

    indicators = set()

    for xx in x:
        indicators.add(xx.indicator)

    assert 'a.clayton10@gmail.com' in indicators
