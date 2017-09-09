import py.test

from csirtg_smrt import Smrt
from csirtg_smrt.rule import Rule
from csirtg_smrt.constants import REMOTE_ADDR
from csirtg_smrt.constants import PYVERSION

rule = 'test/zemail/zemail.yml'
rule = Rule(path=rule)
rule.fetcher = 'stdin'
s = Smrt(REMOTE_ADDR, 1234, client='dummy')


def test_zemail():
    feed = 'abuse'
    with open('test/zemail/single_plain_01.eml') as f:
        data = f.read()

        x = list(s.process(rule, feed=feed, data=data))

        assert len(x) > 0

        assert x[0].indicator == 'http://www.socialservices.cn/detail.php?id=9'
