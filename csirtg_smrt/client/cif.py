import logging
import requests
import time
import json
from csirtg_smrt.exceptions import AuthError
from csirtg_smrt.client.plugin import Client


class CIFClient(Client):

    def __init__(self, remote, token, proxy=None, timeout=300, verify_ssl=True, **kwargs):
        super(CIFClient, self).__init__(remote, token)

        self.remote = remote
        self.token = token
        self.proxy = proxy
        self.timeout = timeout
        self.verify_ssl = verify_ssl

        self.session = requests.Session()
        self.session.headers["Accept"] = 'application/vnd.cif.v3+json'
        self.session.headers['User-Agent'] = 'cifsdk-py/3.0.0a1'
        self.session.headers['Authorization'] = 'Token token=' + self.token
        self.session.headers['Content-Type'] = 'application/json'

    def _post(self, uri, data):
        if type(data) == dict:
            data = json.dumps(data)

        body = self.session.post(uri, data=data)

        if body.status_code > 303:
            err = 'request failed: %s' % str(body.status_code)
            self.logger.debug(err)
            err = body.content

            if body.status_code == 401:
                raise AuthError('unauthorized')
            elif body.status_code == 404:
                err = 'not found'
                raise RuntimeError(err)
            else:
                try:
                    err = json.loads(err).get('message')
                except ValueError as e:
                    err = body.content

                self.logger.error(err)
                raise RuntimeError(err)

        self.logger.debug(body.content)
        body = json.loads(body.content)
        return body

    def indicator_create(self, data):
        data = str(data)

        uri = "{0}/indicators".format(self.remote)
        self.logger.debug(uri)
        rv = self._post(uri, data)
        return rv["data"]

    def ping(self, write=False):
        t0 = time.time()

        uri = '/ping'
        if write:
            uri = '/ping?write=1'

        rv = self._get(uri)

        if rv:
            rv = (time.time() - t0)
            self.logger.debug('return time: %.15f' % rv)

        return rv
