from cifsdk.client.http import HTTP as HTTPClient
import os
import logging
from pprint import pprint
import ujson as json
from cifsdk.exceptions import AuthError
import zlib
from base64 import b64decode
import binascii
import arrow

REMOTE = os.environ.get('CSIRTG_SMRT_CIF_REMOTE', 'http://localhost:5000')

logger = logging.getLogger(__name__)


class CIF(HTTPClient):

    def __init__(self, remote=None, token=None, **kwargs):
        if not remote:
            remote = REMOTE

        super(CIF, self).__init__(remote, token, **kwargs)

        self.session.headers["Accept"] = 'application/vnd.cif.v2+json'
        del self.session.headers['Accept-Encoding']
        #self.nowait = True

    def _get(self, uri, params={}):
        if not uri.startswith('http'):
            uri = self.remote + uri
        body = self.session.get(uri, params=params, verify=self.verify_ssl)

        if body.status_code > 303:
            err = 'request failed: %s' % str(body.status_code)
            logger.error(err)

            if body.status_code == 401:
                raise AuthError('invalid token')
            elif body.status_code == 404:
                err = 'not found'
                raise RuntimeError(err)
            elif body.status_code == 408:
                raise TimeoutError('timeout')
            else:
                try:
                    err = json.loads(body.content).get('message')
                    raise RuntimeError(err)
                except ValueError as e:
                    err = body.content
                    logger.error(err)
                    raise RuntimeError(err)

        data = body.content
        try:
            data = zlib.decompress(b64decode(data))
        except (TypeError, binascii.Error) as e:
            pass
        except Exception as e:
            pass

        msgs = json.loads(data.decode('utf-8'))
        if not msgs.get('data'):
            return msgs

        if isinstance(msgs['data'], list):
            for m in msgs['data']:
                if m.get('message'):
                    try:
                        m['message'] = b64decode(m['message'])
                    except Exception as e:
                        pass
        return msgs

    def indicators_create(self, data):
        if not isinstance(data, list):
            data = [data]

        new = []
        for d in data:
            d = d.__dict__()
            d['observable'] = d.pop('indicator')
            d['otype'] = d.pop('itype')

            if d.get('reporttime'):
                d['reporttime'] = arrow.get(d['reporttime']).datetime.strftime('%Y-%m-%dT%m:%H:%SZ')

            if d.get('lasttime'):
                d['lasttime'] = arrow.get(d['lasttime']).datetime.strftime('%Y-%m-%dT%m:%H:%SZ')

            if d.get('reference'):
                d['altid'] = d['reference']
                d['altid_tlp'] = d.get('reference_tlp')

            new.append(d)

        data = new
        data = json.dumps(data)

        uri = "{0}/observables".format(self.remote)
        logger.debug(uri)

        rv = self._post(uri, data)
        return len(rv)

Plugin = CIF
