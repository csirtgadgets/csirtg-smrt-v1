import py.test

from csirtg_smrt import Smrt
from csirtg_smrt.rule import Rule
from csirtg_smrt.constants import REMOTE_ADDR
from pprint import pprint

rule = 'test/packetmail/packetmail.yml'
rule = Rule(path=rule)
rule.fetcher = 'file'

s = Smrt(REMOTE_ADDR, 1234, client='dummy')


def test_packetmail_iprep():
    rule.feeds['iprep']['remote'] = 'test/packetmail/feed.txt'
    x = s.process(rule, feed="iprep")
    x = list(x)
    assert len(x) > 0

    ips = set()
    tags = set()

    for xx in x:
        ips.add(xx.indicator)
        for t in xx.tags:
            tags.add(t)

    assert '179.40.212.141' in ips
    assert '104.131.128.9' in ips

    assert 'honeynet' in tags
