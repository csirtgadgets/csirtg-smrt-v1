from libtaxii.constants import *
from csirtg_smrt.parser.zstix import (_get_desc_from_stix_indicator, 
    _parse_stix_indicator, _map_stix_to_cif_confidence, _get_tlp_from_xml_stix_package,
    _parse_stix_package)
from csirtg_indicator import Indicator
from urllib.parse import urlparse
from dateutil.tz import tzutc
from datetime import datetime, timedelta
from lxml.etree import fromstring as lxml_fromstring
from stix.core import STIXPackage
import libtaxii as t
import libtaxii.clients as tc
import libtaxii.messages_11 as tm11
import logging
import uuid

logger = logging.getLogger(__name__)

# TAXII v1.1 client
class _TAXII(object):
    __name__ = 'taxii11'

    def __init__(self, **kwargs):

        self.username = kwargs.get('username')
        self.password = kwargs.get('password')
        self.remote = kwargs.get('remote')
        self.key_file = kwargs.get('key_file')
        self.cert_file = kwargs.get('cert_file')
        
        self.client = tc.HttpClient()
        self.up = urlparse(self.remote)
        if self.up.scheme.startswith('https'):
            self.client.set_use_https(True)

        if self.username and self.password:
            self.client.set_auth_type(tc.HttpClient.AUTH_BASIC)
            self.client.set_auth_credentials({
                'username': self.username,
                'password': self.password
            })
        
        # support client cert, default disabled
        if self.key_file and self.cert_file:
            # auth_basic = 1; auth_cert = 2; auth_cert_basic = 3
            if self.client.auth_type:
                self.client.set_auth_type(tc.HttpClient.AUTH_CERT_BASIC)
            else:
                self.client.set_auth_type(tc.HttpClient.AUTH_CERT)

            self.client.auth_credentials.update({
                'key_file': self.key_file,
                'cert_file': self.cert_file 
            })

    def ping(self, write=False):
        raise NotImplemented

    def indicators_create(self, data, **kwargs):
        raise NotImplemented

    
    def _parse_taxii_content(self, taxii_content):
        indicators_to_add = {}
        for stix_obj in taxii_content:
            try:
                stix_parsed = STIXPackage.from_xml(lxml_fromstring(stix_obj.content))
            except Exception as e:
                logger.error('Error parsing STIX object: {}'.format(e))
                continue

            tmp = _parse_stix_package(stix_parsed)
            
            for obs_key, value in tmp.items():
                if obs_key in indicators_to_add:
                    indicators_to_add[obs_key].update(value)
                else:
                    indicators_to_add[obs_key] = value

        for i_dict in indicators_to_add.values():
            if i_dict.get('indicator'):
                logger.debug('adding indicator {}'.format(i_dict['indicator']))
                yield Indicator(**i_dict)


    def indicators(self, collection_name, starttime=(datetime.now(tzutc()) - timedelta(hours=1)),
            endtime=datetime.now(tzutc()),
            subscription_id=None
        ):
        delivery_params = tm11.DeliveryParameters(VID_TAXII_HTTP_10, self.remote, VID_TAXII_XML_11)
        """
        poll_params = tm11.PollParameters(response_type=RT_COUNT_ONLY,
            #content_bindings=[tm11.ContentBinding(CB_STIX_XML_11)], 
            delivery_parameters=delivery_params
            )
        """
        poll_params = tm11.PollRequest.PollParameters()
        poll_req = tm11.PollRequest(message_id=tm11.generate_message_id(),
            collection_name=collection_name,
            exclusive_begin_timestamp_label=starttime,
            inclusive_end_timestamp_label=endtime,
            poll_parameters=poll_params,
            subscription_id=subscription_id
            )

        logger.debug('TAXII collection poll request: {}'.format(poll_req.to_xml(pretty_print=True)))

        poll_req_xml = poll_req.to_xml()
        http_resp = self.client.call_taxii_service2(self.up.hostname,
            self.up.path,
            VID_TAXII_XML_11,
            poll_req_xml,
            self.up.port
            )
        taxii_message = t.get_message_from_http_response(http_resp, poll_req.message_id)

        logger.debug('TAXII collection poll response: {}'.format(taxii_message.to_xml(pretty_print=True)))

        if taxii_message.message_type == MSG_STATUS_MESSAGE:
            if taxii_message.status_type == ST_SUCCESS:
                logger.info('TAXII polled successfully but returned no results')
                return []
            raise RuntimeError('TAXII polling failed: {} - {}'.format(taxii_message.status_type, taxii_message.message))

        return self._parse_taxii_content(taxii_message.content_blocks)
