import py.test

from csirtg_smrt import Smrt
from csirtg_smrt.rule import Rule
from csirtg_smrt.constants import REMOTE_ADDR
from pprint import pprint

rule = 'test/garwarn/garwarn.yml'
rule = Rule(path=rule)
rule.fetcher = 'file'
s = Smrt(REMOTE_ADDR, 1234, client='dummy')


def test_garwarn_urls():
    rule.remote = 'test/garwarn/feed.txt'
    x = s.process(rule, 'urls')
    pprint(x)