from libtaxii.constants import *
from csirtg_indicator.utils import resolve_itype
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
import stix

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
        
        self.CONFIDENCE_MAP = {
            'low': 3,
            'medium': 5,
            'high': 8
        }
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

    def _map_confidence(self, stix_conf=None):
        if not stix_conf:
            stix_conf = 3
            return stix_conf
        
        if isinstance(stix_conf, stix.common.confidence.Confidence):
            stix_conf = str(stix_conf.value)

        try:
            stix_conf = float(stix_conf)
            if stix_conf <=100:
                stix_conf = stix_conf / 10
            elif stix_conf > 100:
                stix_conf = 3
        except:
            stix_conf = stix_conf.lower()
            stix_conf = self.CONFIDENCE_MAP.get(stix_conf, 3)

        return stix_conf

    def _parse_stix_indicator(self, stix_ind_or_obs):
        indicator = None
        if not isinstance(stix_ind_or_obs, dict):
            stix_ind_or_obs = stix_ind_or_obs.to_dict()

        try:
            indicator = stix_ind_or_obs['object']['properties']['value']['value']
        except KeyError:
            # handle obs fqdn embedded in indicator
            if stix_ind_or_obs.get('observable', {}).get('object', {}).get('properties', {}).get('value'):
                indicator = stix_ind_or_obs['observable']['object']['properties']['value']

            # handles obs ipv4/v6 embedded in indicator
            elif stix_ind_or_obs.get('observable', {}).get('object', {}).get('properties', {}).get('address_value'):
                indicator = stix_ind_or_obs['observable']['object']['properties']['address_value']

            # handles obs hashes embedded in indicator
            elif stix_ind_or_obs.get('observable', {}).get('object', {}).get('properties', {}).get('hashes'):
                indicator = stix_ind_or_obs['observable']['object']['properties']['hashes'][0]['simple_hash_value']

            # handles obs email "from" addresses embedded in indicator
            elif stix_ind_or_obs.get('observable', {}).get('object', {}).get('properties', {}).get('header'):
                indicator = stix_ind_or_obs['observable']['object']['properties']['header']['from']['address_value']

            # handles indicator ipv4/v6
            elif stix_ind_or_obs.get('object', {}).get('properties', {}).get('address_value'):
                indicator = stix_ind_or_obs['object']['properties']['address_value']['value']

            # handles indicator hashes
            elif stix_ind_or_obs.get('object', {}).get('properties', {}).get('hashes'):
                indicator = stix_ind_or_obs['object']['properties']['hashes'][0]['simple_hash_value']['value']

            # handles indicator email "from" addresses
            elif stix_ind_or_obs.get('object', {}).get('properties', {}).get('header'):
                indicator = stix_ind_or_obs['object']['properties']['header']['from']['address_value']['value']

        if indicator and not resolve_itype(indicator):
            return None
        return indicator
    
    def _parse_taxii_content(self, taxii_content):
        indicators_to_add = {}
        for stix_obj in taxii_content:
            try:
                stix_parsed = STIXPackage.from_xml(lxml_fromstring(stix_obj.content))
            except Exception as e:
                logger.error('Error parsing STIX object: {}'.format(e))
                continue

            if stix_parsed.indicators:
                for i in stix_parsed.indicators:
                    if not i.observable:
                        continue

                    if i.short_description:
                        description = str(i.short_description.value.lower())
                    elif i.description:
                        description = str(i.description)
                    else:
                        description = None
                    lasttime = i.timestamp or None
                    confidence = self._map_confidence(i.confidence)
                    indicator = self._parse_stix_indicator(i)

                    # save indicator info by its related observable id
                    if indicator:
                        logger.debug('adding indicator {}'.format(indicator))
                    
                    i_dict = {
                        'description': description,
                        'lasttime': lasttime,
                        'confidence': confidence,
                        'indicator': indicator
                    }
                    # if no idref, use the CIF indicator uuid as a unique dict key
                    if not i.observable.idref:
                        idref = str(uuid.uuid4())
                    else:
                        idref = i.observable.idref
                    indicators_to_add[idref] = i_dict

            tlp = None
            try:
                tlp = stix_parsed.stix_header.handling.marking[0].marking_structures[0].color
            except AttributeError:
                pass
                
            if stix_parsed.observables:
                for o in stix_parsed.observables:
                    o = o.to_dict()
                    indicator = self._parse_stix_indicator(o)
                    
                    if not indicator:
                        continue

                    i_dict = { 
                        'indicator': indicator,
                        'tlp': tlp
                    }

                    if indicators_to_add.get(o['id']):
                        indicators_to_add[o['id']].update(i_dict)

        for i_dict in indicators_to_add.values():
            if i_dict.get('indicator'):
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
            poll_req_xml
            )
        taxii_message = t.get_message_from_http_response(http_resp, poll_req.message_id)

        logger.debug('TAXII collection poll response: {}'.format(taxii_message.to_xml(pretty_print=True)))

        if taxii_message.message_type == MSG_STATUS_MESSAGE:
            if taxii_message.status_type == ST_SUCCESS:
                logger.info('TAXII polled successfully but returned no results')
                return []
            raise RuntimeError('TAXII polling failed: {} - {}'.format(taxii_message.status_type, taxii_message.message))

        return self._parse_taxii_content(taxii_message.content_blocks)