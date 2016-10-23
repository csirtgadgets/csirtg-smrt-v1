try:
    import elasticsearch
except ImportError:
    raise ImportError('Requires elasticsearch')

from csirtg_smrt.client.plugin import Client
from pprint import pprint
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl import DocType, String, Date, Integer, Float, Ip, GeoPoint, Index, Mapping
from datetime import datetime
from csirtg_indicator import resolve_itype
import elasticsearch.exceptions
import re
import logging

logger = logging.getLogger(__name__)


class Indicator(DocType):
    indicator = String(index="not_analyzed")
    indicator_ipv4 = Ip()
    group = String(multi=True, index="not_analyzed")
    itype = String(index="not_analyzed")
    tlp = String(index="not_analyzed")
    provider = String(index="not_analyzed")
    portlist = String()
    asn = Float()
    asn_desc = String()
    cc = String()
    protocol = String()
    reporttime = Date()
    lasttime = Date()
    firsttime = Date()
    confidence = Integer()
    timezone = String()
    city = String()
    description = String(index="not_analyzed")
    additional_data = String(multi=True)
    tags = String(multi=True)
    rdata = String(index="not_analyzed")
    message = String(multi=True)


class _ElasticSearch(Client):
    name = 'elasticsearch'

    def __init__(self, remote='localhost:9200', index='indicators', **kwargs):
        super(_ElasticSearch, self).__init__(remote)

        self.index = index
        if isinstance(self.remote, str):
            self.remote = self.remote.split(',')

        connections.create_connection(hosts=self.remote)

    def _create_index(self):
        dt = datetime.utcnow()
        dt = dt.strftime('%Y.%m')
        es = connections.get_connection()
        if not es.indices.exists('indicators-{}'.format(dt)):
            index = Index('indicators-{}'.format(dt))
            index.aliases(live={})
            index.doc_type(Indicator)
            index.create()

            m = Mapping('indicator')
            m.field('indicator_ipv4', 'ip')
            m.field('indicator_ipv4_mask', 'integer')
            m.save('indicators-{}'.format(dt))
        return 'indicators-{}'.format(dt)

    def indicators_create(self, data):
        index = self._create_index()

        doc = data.__dict__()
        del doc['version']

        doc['meta'] = {}
        doc['meta']['index'] = index

        if resolve_itype(data.indicator) == 'ipv4':
            match = re.search('^(\S+)\/(\d+)$', data.indicator)
            if match:
                doc['indicator_ipv4'] = match.group(1)
                doc['indicator_ipv4_mask'] = match.group(2)
            else:
                doc['indicator_ipv4'] = data.indicator

        if type(data.group) != list:
            doc['group'] = [data.group]

        logger.debug(doc)
        i = Indicator(**doc)
        logger.debug(i)
        if i.save():
            return i.__dict__['_d_']
        else:
            raise RuntimeError('unable to save')

Plugin = _ElasticSearch
