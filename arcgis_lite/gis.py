from datetime import datetime, timedelta
from .features import FeatureLayer
from . import requests


__all__ = ['AgolGIS', 'PortalGIS', 'geocode']


class _GIS:
    '''Abstract GIS superclass'''
    def __init__(self, url):
        self.url = url.strip('/')
        self.rest_url = url + '/sharing/rest'
        self._token = None
        self._token_expiration = None

    def feature_layer(self, item_id, layer_number=0):
        '''Get a layer using its feature service item ID'''
        item_data = requests.get(
            self.rest_url + '/content/items/' + item_id,
            params={
                'token': self.token,
                'f': 'json'
            }
        )
        return FeatureLayer(item_data['url'] + '/' + str(layer_number), self)

    def _request_token(self):
        # implemented by subclasses
        pass

    @property
    def token(self):
        '''GIS access token'''
        if not self._token or datetime.utcnow() > self._token_expiration - timedelta(minutes=2):
            self._request_token()
        return self._token

    @property
    def properties(self):
        '''GIS properties'''
        return requests.get(self.rest_url + '/portals/self', {'f': 'json', 'token': self.token})


class AgolGIS(_GIS):
    '''Connection to ArcGIS Online'''
    def __init__(self, username, password, url='https://www.arcgis.com'):
        super().__init__(url)
        self.username = username
        self.password = password

    def _request_token(self):
        token_data = requests.post(
            self.rest_url + '/generateToken',
            data={
                'username': self.username,
                'password': self.password,
                'referer': self.url,
                'f': 'json'
            }
        )
        self._token = token_data['token']
        self._token_expiration = datetime.utcfromtimestamp(int(token_data['expires'] / 1000))


class PortalGIS(_GIS):
    '''Connection to ArcGIS Enterprise Portal'''
    def __init__(self, url, client_id, refresh_token):
        super().__init__(url)
        self.client_id = client_id
        self.refresh_token = refresh_token

    def _request_token(self):
        token_data = requests.get(
            self.rest_url + '/oauth2/token',
            params={
                'grant_type': 'refresh_token',
                'client_id': self.client_id,
                'refresh_token': self.refresh_token,
                'f': 'json'
            }
        )
        self._token = token_data['access_token']
        self._token_expiration = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])


def geocode(address, city, state, zipcode=None, county=None, **kwargs):
    '''Geocode an address'''
    query_params = {
        'address': address,
        'city': city,
        'region': state,
        'postal': zipcode,
        'subregion': county,
        'countryCode': 'USA',
        'maxLocations': 1,
        'outSR': 4326,
        'f': 'json'
    }
    query_params.update(kwargs)
    geocode_result = requests.get(
        'https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates',
        query_params
    )
    return geocode_result
