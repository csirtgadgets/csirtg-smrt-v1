import py.test

from csirtg_smrt import Smrt
from csirtg_smrt.rule import Rule
from csirtg_smrt.constants import REMOTE_ADDR
from pprint import pprint
import re

rule = 'test/csirtg/csirtg.yml'
rule = Rule(path=rule)
rule.fetcher = 'file'

s = Smrt(REMOTE_ADDR, 1234, client='dummy')


def test_csirtg_portscanners():
    rule.feeds['port-scanners']['remote'] = 'test/csirtg/feed.txt'
    x = s.process(rule, feed="port-scanners")
    x = list(x)
    assert len(x) > 0

    ips = set()
    tags = set()

    for xx in x:
        ips.add(xx.indicator)
        tags.add(xx.tags[0])

    assert '109.111.134.64' in ips
    assert 'scanner' in tags


def test_csirtg_skips():
    rule.feeds['port-scanners']['remote'] = 'test/csirtg/feed.txt'
    rule['skip'] = '216.121.233.27'

    x = s.process(rule, feed="port-scanners")
    x = list(x)
    assert len(x) > 0

    ips = set()

    for xx in x:
        ips.add(xx.indicator)

    assert '216.121.233.27' not in ips

    ips = set()

    del rule['skip']
    rule.feeds['port-scanners']['skip'] = '216.121.233.27'

    x = s.process(rule, feed="port-scanners")
    x = list(x)
    assert len(x) > 0

    ips = set()

    for xx in x:
        ips.add(xx.indicator)

    assert '216.121.233.27' not in ips