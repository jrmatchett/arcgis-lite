from datetime import datetime, timedelta
from .features import FeatureLayer
from . import _requests


__all__ = ['AgolGIS', 'PortalGIS']


class _GIS:
    '''Abstract GIS superclass'''
    def __init__(self, url):
        self.url = url.strip('/')
        self.rest_url = url + '/sharing/rest'
        self._token = None
        self._token_expiration = None
        self._geocoder = None
        self._properties = None

    def __repr__(self):
        return f"GIS @ {self.url}"

    def feature_layer(self, item_id, layer_number=0):
        '''Get a layer using its feature service item ID'''
        item_data = _requests.get(
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

    def geocode(self, full_address=None, **kwargs):
        '''Geocode a single address. Provide either a single-line address or address components
        using the API keywords, such as address, city, region, postal. See findAddressCandidates
         in the ArcGIS REST API documentation for accepted parameters.
        '''
        query_params = {
            'maxLocations': 1,
            'outSR': 4326,
            'f': 'json',
            'token': self.token
        }
        if full_address:
            query_params['singleLine'] = full_address
        query_params.update(kwargs)
        return _requests.get(self.geocoder + '/findAddressCandidates', query_params)

    def batch_geocode(self, addresses, **kwargs):
        '''Geocode addresses. Provide a list of single-line addresses. See geocodeAddresses in
        the ArcGIS REST API documentation for accepted parameters.
        '''
        records = [{'attributes': {'OBJECTID': i, 'singleLine': a}} for i, a in enumerate(addresses)]
        data = {
            'addresses': {'records': records},
            'outSR': 4326,
            'f': 'json',
            'token': self.token
        }
        data.update(kwargs)
        return _requests.post(self.geocoder + '/geocodeAddresses', data)

    @property
    def token(self):
        '''GIS access token'''
        if not self._token or datetime.utcnow() > self._token_expiration - timedelta(minutes=2):
            self._request_token()
        return self._token

    @property
    def properties(self):
        '''GIS properties'''
        if not self._properties:
            self._properties = _requests.get(
                self.rest_url + '/portals/self',
                {'f': 'json', 'token': self.token}
            )
        return self._properties

    @property
    def geocoder(self):
        '''URL of geocoding service'''
        if not self._geocoder:
            geocoders = self.properties['helperServices']['geocode']
            # prefer a geocoder that can batch geocode
            for geocoder in geocoders:
                if geocoder['batch']:
                    self._geocoder = geocoder['url']
                    break
                else:
                    self._geocoder = geocoder['url']
        return self._geocoder


class AgolGIS(_GIS):
    '''Connection to ArcGIS Online'''
    def __init__(self, username, password, url='https://www.arcgis.com'):
        super().__init__(url)
        self.username = username
        self.password = password

    def _request_token(self):
        token_data = _requests.post(
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
    def __init__(self, url, client_id, refresh_token=None):
        super().__init__(url)
        self.client_id = client_id
        if refresh_token:
            self.refresh_token = refresh_token
        else:
            import webbrowser
            from urllib.parse import urlencode
            params = {
                'client_id': client_id,
                'response_type': 'code',
                'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
                'expiration': 1440
            }
            auth_url = self.rest_url + '/oauth2/authorize?' + urlencode(params)
            webbrowser.open(auth_url)
            auth_code = input('Enter Approval Code: ')
            data = {
                'client_id': client_id,
                'grant_type': 'authorization_code',
                'code': auth_code,
                'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
                'f': 'json'
            }
            auth_response = _requests.post(self.rest_url + '/oauth2/token', data)
            self._token = auth_response['access_token']
            self.refresh_token = auth_response['refresh_token']
            self._token_expiration = datetime.utcnow() + timedelta(seconds=auth_response['expires_in'])

    def _request_token(self):
        token_data = _requests.get(
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
