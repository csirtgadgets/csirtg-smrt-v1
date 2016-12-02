import py.test

from csirtg_smrt import Smrt
from csirtg_smrt.rule import Rule
from csirtg_smrt.constants import REMOTE_ADDR
from pprint import pprint

rule = 'test/bambenek/bambenek.yml'
rule = Rule(path=rule)
rule.fetcher = 'file'

s = Smrt(REMOTE_ADDR, 1234, client='dummy')


def test_bambenek_fqdn():
    rule.feeds['c2-dommasterlist']['remote'] = 'test/bambenek/fqdn_feed.txt'
    x = s.process(rule, feed="c2-dommasterlist")
    x = list(x)
    assert len(x) > 0

    indicators = set()
    tags = set()

    for xx in x:
        indicators.add(xx.indicator)
        tags.add(xx.tags[0])
        assert xx.lasttime
        assert xx.description
        assert xx.altid
        assert xx.provider
        assert xx.confidence
        assert xx.tags

    assert 'drohppbkxj.com' in indicators
    assert 'inbxvqkegoyapgv.com' in indicators

    assert 'botnet' in tags


def test_bambenek_ipv4():
    rule.feeds['c2-ipmasterlist']['remote'] = 'test/bambenek/ipv4_feed.txt'
    x = s.process(rule, feed="c2-ipmasterlist")
    x = list(x)
    assert len(x) > 0

    indicators = set()
    tags = set()

    for xx in x:
        indicators.add(xx.indicator)
        tags.add(xx.tags[0])
        assert xx.lasttime
        assert xx.description
        assert xx.altid
        assert xx.provider
        assert xx.confidence
        assert xx.tags

    assert '141.8.225.68' in indicators
    assert '185.28.193.192' in indicators

    assert 'botnet' in tags
