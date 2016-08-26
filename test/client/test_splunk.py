import pytest
import os
from csirtg_smrt import Smrt
from pprint import pprint

REMOTE = os.environ.get('CSIRTG_SMRT_SPLUNK_NODES', 'localhost:9200')

@pytest.mark.skip(reason="no way of currently testing this")
def test_smrt_splunk():
    with Smrt(remote=REMOTE, client='splunk') as s:
        assert type(s) is Smrt

        x = s.process('test/smrt/rules/csirtg.yml', feed='port-scanners')
        assert len(x) > 0
