import py.test

from csirtg_smrt import Smrt
from csirtg_smrt.rule import Rule
from csirtg_smrt.constants import REMOTE_ADDR

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
    rule.skip = '216.121.233.27'

    x = s.process(rule, feed="port-scanners")
    x = list(x)
    assert len(x) > 0

    ips = set()

    for xx in x:
        ips.add(xx.indicator)

    assert '216.121.233.27' not in ips

    ips = set()

    rule.skip = None
    rule.feeds['port-scanners']['skip'] = '216.121.233.27'

    x = s.process(rule, feed="port-scanners")
    x = list(x)
    assert len(x) > 0

    ips = set()

    for xx in x:
        ips.add(xx.indicator)

    assert '216.121.233.27' not in ips


def test_csirtg_skips_quotes():
    rule.feeds['port-scanners']['remote'] = 'test/csirtg/feed2_csv.txt'
    rule.skip_first = True
    rule['skip'] = '216.243.31.2'

    x = s.process(rule, feed="port-scanners")
    x = list(x)
    assert len(x) > 0

    ips = set()

    for xx in x:
        ips.add(xx.indicator)

    assert '216.121.233.27' not in ips


def test_csirtg_skips_first():
    rule.feeds['port-scanners']['remote'] = 'test/csirtg/feed2_csv.txt'
    rule.feeds['port-scanners']['skip_first'] = True

    x = s.process(rule, feed="port-scanners")
    x = list(x)
    assert len(x) == 3


def test_csirtg_limits():
    rule.feeds['port-scanners']['remote'] = 'test/csirtg/feed2_csv.txt'
    rule.feeds['port-scanners']['limit'] = 1

    x = s.process(rule, feed="port-scanners")
    x = list(x)
    assert len(x) == 1
