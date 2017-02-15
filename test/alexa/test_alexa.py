import py.test

from csirtg_smrt import Smrt
from csirtg_smrt.rule import Rule
from csirtg_smrt.constants import REMOTE_ADDR
from pprint import pprint

rule = 'test/alexa/alexa.yml'
rule = Rule(path=rule)
rule.fetcher = 'file'

s = Smrt(REMOTE_ADDR, 1234, client='dummy')


def test_alexa_top1m():
    r, feed = next(s.load_feeds(rule, feed='topN'))

    r.defaults['remote'] = 'test/alexa/alexa_top-1m.csv.zip'
    x = s.process(r, feed)
    x = list(x)
    assert len(x) > 0
    
    assert x[0].indicator == "google.com"
    assert x[1].indicator == "youtube.com"
    
    assert int(x[0].confidence) == 95
    assert int(x[9].confidence) == 95
    assert int(x[10].confidence) == 75
    assert int(x[99].confidence) == 75
    assert int(x[100].confidence) == 50
    assert int(x[999].confidence) == 50
    assert int(x[1000].confidence) == 25
    assert int(x[9999].confidence) == 25
    assert int(x[10000].confidence) == 0

    assert len(x) == 10100
    
    tags = set()
    for xx in x:
        assert xx.indicator
        assert xx.description
        assert xx.tags
        assert xx.application
        assert xx.protocol
        assert xx.altid
        assert xx.provider
        assert xx.tlp
        assert xx.altid_tlp
        assert xx.confidence >= 0
        
        tags.add(*xx.tags)
        
    assert 'whitelist' in tags
