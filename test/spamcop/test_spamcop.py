import py.test

from csirtg_smrt import Smrt
from csirtg_smrt.rule import Rule
from csirtg_smrt.constants import REMOTE_ADDR
from csirtg_smrt.constants import PYVERSION

rule = 'test/spamcop/spamcop.yml'
rule = Rule(path=rule)
rule.fetcher = 'stdin'
s = Smrt(REMOTE_ADDR, 1234, client='dummy')


def test_spamcop():
    feed = 'abuse'
    rule.feeds[feed]['remote'] = 'stdin'
    with open('test/spamcop/email1.txt') as f:
        data = f.read()

        x = list(s.process(rule, feed=feed, data=data))

        assert len(x) > 0

        assert len(x[0].indicator) > 4

        assert x[0].indicator == '204.93.2.6'

        if PYVERSION == 2:
            assert x[0].message.startswith('From: xxx@reports.spamcop.net\nT')
        else:
            assert x[0].message.startswith('From: xxx@reports.spamcop.net\nT')