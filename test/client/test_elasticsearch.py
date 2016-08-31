import pytest
import os
from csirtg_smrt import Smrt
from elasticsearch_dsl.connections import connections
import elasticsearch
from pprint import pprint

REMOTE = os.environ.get('CSIRTG_SMRT_ELASTICSEARCH_NODES', 'localhost:9200')
ES_TESTS = os.environ.get('CSIRTG_SMRT_ES_TESTS', False)


@pytest.mark.skipif(ES_TESTS is False, reason='CSIRTG_SMRT_ES_TESTS not set to True')
def test_smrt_elastcisearch():
    with Smrt(remote=REMOTE, client='elasticsearch') as s:
        assert type(s) is Smrt

        x = s.process('test/smrt/rules/csirtg.yml', feed='port-scanners')
        assert len(x) > 0

        x = s.process('test/smrt/rules/csirtg.yml', feed='port-scanners')
        assert len(x) > 0

        # cleanup
        es = connections.get_connection()
        cli = elasticsearch.client.IndicesClient(es)
        cli.delete(index='indicators-*')
