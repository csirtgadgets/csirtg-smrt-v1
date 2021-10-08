import copy
import uuid
import os
from stix.core import STIXPackage
from stix.common.confidence import Confidence as STIX_Confidence
from pprint import pprint
from csirtg_smrt.parser import Parser
from csirtg_indicator.utils import resolve_itype


def _parse_stix_indicator(stix_ind_or_obs, expected_itype=None):
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
        elif isinstance(stix_ind_or_obs.get('observable', {}).get('object', {}).get('properties', {}).get('address_value'), str):
            indicator = stix_ind_or_obs['observable']['object']['properties']['address_value']

        # handles obs ipv4/v6 embedded in indicator
        elif stix_ind_or_obs.get('observable', {}).get('object', {}).get('properties', {}).get('address_value', {}).get('value'):
            indicator = stix_ind_or_obs['observable']['object']['properties']['address_value']['value']

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

    
    if indicator:
        itype = resolve_itype(indicator)
        if not itype:
            indicator = None
        elif expected_itype and expected_itype != itype:
            indicator = None

    return indicator


def _get_desc_from_stix_indicator(stix_indicator):
    description = None
    if stix_indicator.short_description:
        description = str(stix_indicator.short_description.value.lower())
    elif stix_indicator.description:
        description = str(stix_indicator.description)
    elif stix_indicator.title:
        description = str(stix_indicator.title.lower())
    
    return description


def _get_tlp_from_xml_stix_package(stix_package):
    tlp = None
    try:
        tlp = stix_package.stix_header.handling.marking[0].marking_structures[0].color
    except AttributeError:
        pass

    return tlp


def _map_stix_to_cif_confidence(stix_indicator):
    if not stix_indicator.confidence:
        stix_conf = None
        return stix_conf

    stix_conf = stix_indicator.confidence
    
    if isinstance(stix_conf, STIX_Confidence):
        stix_conf = str(stix_conf.value)

    try:
        stix_conf = float(stix_conf)
        if stix_conf <=100:
            stix_conf = stix_conf / 10
        elif stix_conf > 100:
            stix_conf = 3
    except:
        CONFIDENCE_MAP = {
            'low': 3,
            'medium': 5,
            'high': 8
        }
        stix_conf = stix_conf.lower()
        stix_conf = CONFIDENCE_MAP.get(stix_conf, None)

    return stix_conf


def _parse_stix_package(stix_package, indicator_template=None, expected_itype=None):
    indicators_to_add = {}
    tlp = _get_tlp_from_xml_stix_package(stix_package)
    if stix_package.indicators:
        for i in stix_package.indicators:
            if not i.observable:
                continue

            description = _get_desc_from_stix_indicator(i)
            lasttime = i.timestamp or None
            confidence = _map_stix_to_cif_confidence(i)
            indicator = _parse_stix_indicator(i, expected_itype)

            i_dict = {}

            if description:
                i_dict['description'] = description 
            if lasttime:
                i_dict['lasttime'] = lasttime
            if confidence:
                i_dict['confidence'] = confidence
            if tlp:
                i_dict['tlp'] = tlp

            # override i_dict w/ smrt rule settings if available
            if indicator_template:
                i_dict.update(indicator_template)

            # but don't override indicator
            if indicator:
                i_dict['indicator'] = indicator
            
            # if no idref, generate a uuid as a unique dict key
            if not i.observable.idref:
                idref = str(uuid.uuid4())
            else:
                idref = i.observable.idref
            
            indicators_to_add[idref] = i_dict
        
    if stix_package.observables:
        for o in stix_package.observables:
            o = o.to_dict()
            indicator = _parse_stix_indicator(o)
            
            if not indicator:
                continue

            i_dict = { 
                'indicator': indicator,
            }
            if tlp:
                i_dict['tlp'] = tlp

            idref = o['id']
            
            if indicators_to_add.get(idref):
                indicators_to_add[idref].update(i_dict)
            else:
                if indicator_template:
                    i_dict.update(indicator_template)
                indicators_to_add[idref] = i_dict

    return indicators_to_add


class Stix(Parser):

    def __init__(self, *args, **kwargs):
        super(Stix, self).__init__(*args, **kwargs)


    def process(self):
        defaults = self._defaults()
        indicators_to_add = {}

        try:
            feed = STIXPackage.from_xml(self.rule.remote)
        except Exception as e:
            self.logger.error('Error parsing feed {}: {}'.format(self.rule.remote, e))
            raise e

        indicators_to_add.update(_parse_stix_package(
            feed,
            indicator_template=copy.deepcopy(defaults),
            expected_itype=self.itype
            ))

        for i_dict in indicators_to_add.values():
            if i_dict.get('indicator'):
                yield i_dict

Plugin = Stix
