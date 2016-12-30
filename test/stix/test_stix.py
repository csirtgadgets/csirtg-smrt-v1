import pytest

from csirtg_smrt import Smrt
from csirtg_smrt.rule import Rule
from csirtg_smrt.constants import REMOTE_ADDR
from pprint import pprint
import os

DISABLE_TESTS = True
if os.environ.get('CSIRTG_SMRT_STIX_TEST'):
    if os.environ['CSIRTG_SMRT_STIX_TEST'] == '1':
        DISABLE_TESTS = False

if not DISABLE_TESTS:
    try:
        from stix.core import STIXPackage
    except ImportError:
        raise ImportError('STIX not installed by default, install using `pip install stix`')


rule = 'test/stix/test.yml'
rule = Rule(path=rule)
rule.fetcher = 'file'
s = Smrt(REMOTE_ADDR, 1234, client='dummy')


@pytest.mark.skipif(DISABLE_TESTS, reason='need to set CSIRTG_SMRT_STIX_TEST=1 to run')
def test_stix():
    rule.remote = 'test/stix/feed.xml'
    x = s.process(rule, feed='fqdn')
    x = list(x)

    assert len(x) > 0
    assert len(x[0].indicator) > 4

    indicators = set()
    for xx in x:
        indicators.add(xx.indicator)

    assert 'http://efax.pfdregistry.org/efax/37486.zip' in indicators
