from datetime import datetime, timedelta
from .features import FeatureLayer
from . import _requests


__all__ = ['GIS']


class GIS:
    '''Connection to an ArcGIS portal'''
    def __init__(self,
        url='https://www.arcgis.com',
        username=None, password=None,
        client_id=None, client_secret=None,
        refresh_token=None,
        refresh_expiration=20160
    ):
        self.username = username
        self.password = password
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.refresh_expiration = refresh_expiration
        self.url = url.strip('/')
        self.rest_url = self.url + '/sharing/rest'
        self._token = None
        self._token_expiration = None
        self._geocoder = None
        self._properties = None

        if client_id and not client_secret and not refresh_token:
            self._request_token()

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
        if self.username and self.password:
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

        elif self.client_id and not self.client_secret and not self.refresh_token:
            import webbrowser
            from urllib.parse import urlencode
            params = {
                'client_id': self.client_id,
                'response_type': 'code',
                'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob'
            }
            auth_url = self.rest_url + '/oauth2/authorize?' + urlencode(params)
            webbrowser.open(auth_url)
            auth_code = input('Enter Approval Code: ')
            data = {
                'client_id': self.client_id,
                'grant_type': 'authorization_code',
                'code': auth_code,
                'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
                'expiration': self.refresh_expiration,
                'f': 'json'
            }
            auth_response = _requests.post(self.rest_url + '/oauth2/token', data)
            self._token = auth_response['access_token']
            self.refresh_token = auth_response['refresh_token']
            self._token_expiration = datetime.utcnow() + timedelta(seconds=auth_response['expires_in'])

        elif self.client_id and self.client_secret:
            token_data = _requests.post(
                self.rest_url + '/oauth2/token',
                data={
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'grant_type': 'client_credentials',
                    'f': 'json'
                }
            )
            self._token = token_data['access_token']
            self._token_expiration = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])

        elif self.client_id and self.refresh_token:
            token_data = _requests.post(
                self.rest_url + '/oauth2/token',
                data={
                    'client_id': self.client_id,
                    'grant_type': 'refresh_token',
                    'refresh_token': self.refresh_token,
                    'f': 'json'
                }
            )
            self._token = token_data['access_token']
            self._token_expiration = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])

        else:
            raise RuntimeError('Credentials are incomplete. Provide either a combination of username'\
                '/password, client_id/client_secret, or client_id/refresh_token')

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
            'outFields': 'Addr_type',
            'f': 'json',
            'token': self.token
        }
        data.update(kwargs)
        geocodes = _requests.post(self.geocoder + '/geocodeAddresses', data)
        for gc in geocodes['locations']:
            record = records[gc['attributes']['ResultID']]
            record['attributes']['match_address'] = gc['address']
            record['attributes']['search_address'] = record['attributes'].pop('singleLine')
            record['attributes'].update(gc['attributes'])
            record['geometry'] = gc['location']
            record['geometry']['spatialReference'] = geocodes['spatialReference']
        return records

    def reverse_geocode(self, x, y=None, **kwargs):
        '''Reverse geocode a single point. Provide either longitude and latitude coordinates or
        an ArcGIS point geometry dictionary. See reverseGeocode in the ArcGIS REST API documentation
        for other accepted parameters.
        '''
        query_params = {
            'location': x if isinstance(x, dict) else f'{x},{y}',
            'f': 'json',
            'token': self.token
        }
        query_params.update(kwargs)
        return _requests.get(self.geocoder + '/reverseGeocode', query_params)

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
