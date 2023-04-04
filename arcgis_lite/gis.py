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
            if 'location' in gc:
                record['geometry'] = gc['location']
                record['geometry']['spatialReference'] = geocodes['spatialReference']
            else:
                record['geometry'] = None
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

    def census_geocode(self, addresses, return_type='list'):
        '''Geocodes addresses using the US Census Bureau's batch geocoding service.

        Addresses without a match are subsequently geocoded with the GIS's
        service. This method reduces service credits consumption, but is
        much slower than Esri's service. Around 20% of addresses fail to
        match using the US Census service.

        Arguments:
        addresses    A list of addresses. Each address must be a dictionary
                        with 'Address', 'City', 'Region' (2-letter state), and
                        'Postal' (zipcode) items. Maximum list size is 1000.
        return_type  'list' returns a list of dictionaries, while 'gdf'
                        returns an geopandas GeoDataFrame.

        Returns:  A list of dictionaries, each containing 'address',
                    'match_type', 'source', and 'location' items; or a
                    spatially-enabled dataframe with 'address', 'match_type',
                    'source', and 'SHAPE' columns.
        '''
        import io
        import tempfile
        import pandas as pd
        import requests

        # check batch size limit
        if len(addresses) > 1000:
            raise ValueError('Number of addresses must not exceed 1000.')

        # batch geocode with US Census Bureau service
        adds_df = pd.DataFrame(addresses)
        with tempfile.NamedTemporaryFile(suffix='.csv') as f:
            adds_df.to_csv(
                f.name,
                columns=['Address', 'City', 'Region', 'Postal'],
                header=False
            )
            census_gc = requests.post(
                url='https://geocoding.geo.census.gov/geocoder/locations/addressbatch',
                params={'returntype': 'locations', 'benchmark': 'Public_AR_Current'},
                files={'addressFile': f}
            )
        census_df = pd.read_csv(
            io.StringIO(census_gc.text),
            header=None,
            names=['id','input_address','match_indicator','match_type','match_address','lon_lat','tigerline_id','tigerline_side']
        )
        adds_df = adds_df.join(census_df[['id', 'match_indicator', 'match_type', 'match_address', 'lon_lat']].set_index('id'))

        # create output list
        adds_out = []
        for _, a in adds_df.iterrows():
            if pd.isnull(a.match_address):
                # geocode address with RC View service
                gis_gc = self.geocode(
                    **dict(a[['Address', 'City', 'Region', 'Postal']]),
                    outFields='Addr_type,StAddr,City,RegionAbbr,Postal',
                    maxLocations=1,
                    forStorage=False,
                    outSR=4326
                )
                if gis_gc:
                    gis_gc0 = gis_gc['candidates'][0]
                    gc_atts = gis_gc0['attributes']
                    add_comps = []
                    if gc_atts['StAddr'] != '':
                        add_comps.append(gc_atts['StAddr'])
                    if gc_atts['City'] != '':
                        add_comps.append(gc_atts['City'])
                    if gc_atts['RegionAbbr'] != '':
                        add_comps.append(gc_atts['RegionAbbr'])
                    if gc_atts['Postal'] != '':
                        add_comps.append(gc_atts['Postal'])
                    add_dict = {
                        'address': ', '.join(add_comps).upper(),
                        'match_type': gc_atts['Addr_type'],
                        'source': 'Esri',
                        'location': {
                            'x': round(gis_gc0['location']['x'], 6),
                            'y': round(gis_gc0['location']['y'], 6),
                            'spatialReference': {'wkid': 4326}
                        }
                    }
                else: # no address match
                    add_dict = {
                        'address': None,
                        'match_type': 'No_Match',
                        'source': 'Esri',
                        'location': None
                    }
            else:
                # US Census match
                coords = a.lon_lat.split(',')
                add_dict = {
                    'address': a.match_address,
                    'match_type': a.match_type,
                    'source': 'US Census',
                    'location': {
                        'x': float(coords[0]),
                        'y': float(coords[1]),
                        'spatialReference': {'wkid': 4326}
                    }
                }
            adds_out.append(add_dict)

        if return_type == 'gdf':
            import geopandas as gpd
            from shapely.geometry import Point
            points = [Point(i['location']['x'], i['location']['y']) for i in adds_out]
            return gpd.GeoDataFrame(
                data=gpd.pd.DataFrame(adds_out).drop(columns='location'),
                geometry=points,
                crs='EPSG:4326'
            )
        else:
            return adds_out

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
