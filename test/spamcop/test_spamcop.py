import py.test

from csirtg_smrt import Smrt
from csirtg_smrt.rule import Rule
from csirtg_smrt.constants import REMOTE_ADDR

rule = 'test/spamcop/spamcop.yml'
rule = Rule(path=rule)
rule.fetcher = 'stdin'
s = Smrt(REMOTE_ADDR, 1234, client='dummy')


def test_spamcop():
    rule.feeds[feed]['remote'] = 'test/spamcop/email1.txt'
    x = s.process(rule, feed=feed)
    assert len(x) > 0

    assert len(x[0].indicator) > 4
