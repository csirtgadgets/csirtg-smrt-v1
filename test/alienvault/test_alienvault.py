import py.test

from csirtg_smrt import Smrt
from csirtg_smrt.rule import Rule
from csirtg_smrt.constants import REMOTE_ADDR
from pprint import pprint

rule = 'test/alienvault/alienvault.yml'
rule = Rule(path=rule)
rule.fetcher = 'file'

s = Smrt(REMOTE_ADDR, 1234, client='dummy')


def test_alienvault_scanners():
    rule.feeds['scanners']['remote'] = 'test/alienvault/feed.txt'
    x = s.process(rule, feed="scanners")
    x = list(x)
    assert len(x) > 0

    ips = set()
    tags = set()

    for xx in x:
        ips.add(xx.indicator)
        tags.add(xx.tags[0])

    assert '114.143.191.19' in ips
    assert '180.97.215.63' in ips

    assert 'scanner' in tags


def test_alienvault_spammers():
    rule.feeds['spammers']['remote'] = 'test/alienvault/feed.txt'
    x = s.process(rule, feed="spammers")
    x = list(x)
    assert len(x) > 0

    ips = set()
    tags = set()

    for xx in x:
        ips.add(xx.indicator)
        tags.add(xx.tags[0])

    assert '23.92.83.73' in ips
    assert '93.127.228.36' in ips

    assert 'spam' in tags


def test_alienvault_malware():
    rule.feeds['malware']['remote'] = 'test/alienvault/feed.txt'
    x = s.process(rule, feed="malware")
    x = list(x)
    assert len(x) > 0

    ips = set()
    tags = set()

    for xx in x:
        ips.add(xx.indicator)
        tags.add(xx.tags[0])

    assert '93.158.211.210' in ips

    assert 'malware' in tags
