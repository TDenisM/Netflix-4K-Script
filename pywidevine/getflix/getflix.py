"""Hijack urllib3's dns resolver and getflix.com.au api"""
from socket import error as SocketError, timeout as SocketTimeout
import json
import logging
import time

from urllib3.connection import HTTPConnection
from urllib3.util import connection
from urllib3.exceptions import ConnectTimeoutError
from urllib3.exceptions import NewConnectionError
import requests
import dns.resolver

GETFLIX_DNSSERV = ['54.164.176.2', '54.187.61.200']

def getflix_new_conn(self):
    """ Establish a socket connection and set nodelay settings on it.
    :return: New socket connection.
    """
    extra_kw = {}
    if self.source_address:
        extra_kw['source_address'] = self.source_address

    if self.socket_options:
        extra_kw['socket_options'] = self.socket_options

    hostname = getflix_lookup(self.host)
    try:
        conn = connection.create_connection(
            (hostname, self.port), self.timeout, **extra_kw)

    except SocketTimeout as err:
        raise ConnectTimeoutError(
            self, "Connection to %s timed out. (connect timeout=%s)" %
            (self.host, self.timeout))

    except SocketError as err:
        raise NewConnectionError(
            self, "Failed to establish a new connection: %s" % err)

    return conn

def getflix_lookup(host):
    """resolve a dns address"""
    res = dns.resolver.Resolver()
    res.nameservers = GETFLIX_DNSSERV
    answers = res.query(host, 'A')
    for rdata in answers:
        return str(rdata)

class Getflix(object):
    """interface for getflix"""

    API_URL = 'https://www.getflix.com.au/api/'
    ENDPOINTS = {
        'region': 'v1/regions.json',
        'region_list': 'v1/regions/list.json',
        'ip': 'v1/addresses.json',
        'profile': 'v1/profile.json',
        'subscription': 'v1/subscription.json',
        'system': 'v1/system.json',
    }

    _old_conn = None

    def __init__(self, apikey):
        """set auth information"""
        self.logger = logging.getLogger(__name__)
        self.auth = (apikey, 'x')

    def enable(self):
        """enable getflix lookups"""
        self.logger.info("hijacking dns lookups")
        self.logger.debug("saving old HTTPConnection._new_conn: {}".format(HTTPConnection._new_conn))
        self._old_conn = HTTPConnection._new_conn
        self.logger.debug("setting new HTTPConnection._new_conn: {}".format(getflix_new_conn))
        HTTPConnection._new_conn = getflix_new_conn

    def disable(self):
        """disable getflix lookups"""
        self.logger.debug("restoring HTTPConnection._new_conn")
        HTTPConnection._new_conn = self._old_conn

    def lookup(self, host):
        """perform a getflix lookup"""
        self.logger.info("looking up address")
        return getflix_lookup(host)

    def region_list(self):
        """return getflix region list"""
        req = requests.get(self.API_URL+self.ENDPOINTS['region_list'],
                           auth=self.auth)
        return json.loads(req.text)

    def region_get(self, curr_service):
        """get the current region"""
        while True:
            try:
                req = requests.get(self.API_URL+self.ENDPOINTS['region'],
                            auth=self.auth)
                break
            except:
                time.sleep(10)
                continue
        for service in json.loads(req.text):
            if service['service'] == curr_service:
                if service['region'] == 'GB':
                    return 'UK'
                else:
                    return service['region']
        return None

    def region_set(self, service, region):
        """set the region"""
        self.logger.info("updating getflix region for service {} to {}".format(service, region))
        if service == 'prime' and region == 'UK':
            region = 'GB'
        data = {'service': service, 'region': region}
        req = requests.post(self.API_URL+self.ENDPOINTS['region'],
                            data=json.dumps(data),
                            auth=self.auth)
        resp = json.loads(req.text)
        try:
            if resp['region'] == region:
                return True
            else:
                self.logger.error("updating getflix region failed")
                return False
        except:
            self.logger.error("updating getflix region failed")
            return False

    def update_ip(self):
        """updates auth'd ip"""
        self.logger.info("updating getflix ip")
        req = requests.put(self.API_URL+self.ENDPOINTS['ip'],
                           auth=self.auth)
        if req.status_code == 200:
            return True
        else:
            self.logger.error("updating getflix ip failed")
            return False
