import pytest
import os
from csirtg_smrt import Smrt
from csirtgsdk.client import Client as CSIRTGClient
from csirtgsdk.feed import Feed
from pprint import pprint

CSIRTGIO_TESTS = os.environ.get('CSIRTG_SMRT_CSIRTGIO_TESTS', False)
USERNAME = os.environ.get('CSIRTG_SMRT_CSIRTGIO_USERNAME', 'wes')
TOKEN = os.environ.get('CSIRTG_SMRT_CSIRTGIO_TOKEN', False)
FEED = os.environ.get('CSIRTG_SMRT_CSIRTGIO_FEED', 'csirtg_smrt_test')


@pytest.mark.skipif(CSIRTGIO_TESTS is False, reason='CSIRTG_SMRT_CSIRTGIO_TESTS not set to True')
def test_client_csirtg():
    with Smrt(client='csirtg', username=USERNAME, feed='csirtg_smrt_test', token=TOKEN) as s:
        assert type(s) is Smrt

        # create test feed
        cli = CSIRTGClient(token=TOKEN)
        f = Feed(cli).new(USERNAME, FEED)
        assert f
        assert f['user'] == USERNAME

        x = s.process('test/smrt/rules/csirtg.yml', feed='port-scanners')
        assert len(x) > 0

        # remove test feed
        f = Feed(cli).remove(USERNAME, FEED)
        assert f == 200
