import logging
import requests
import time
import json
from csirtg_smrt.exceptions import AuthError
from csirtg_indicator import Indicator
from pprint import pprint

from .plugin import Client
from csirtgsdk.client import Client as CSIRTGClient


class CIFClient(Client, CSIRTGClient):

    def ping(self):
        return self.get('https://csirtg.io/api')

    def indicator_create(self, data, user, feed):
        self.submit_bulk(data, user, feed)
