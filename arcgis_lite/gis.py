import datetime
from features import FeatureLayer
from url_requests import url_get, url_post


class _GIS:
    '''Abstract GIS superclass'''
    def __init__(self, url):
        self.url = url.strip('/')
        self.rest_url = url + '/sharing/rest'
        self._token = None
        self.token_expiration = None

    def _get_token(self):
        # implemented by subclasses
        pass

    def feature_layer(self, item_id, layer_number=0):
        item_data = url_get(
            self.rest_url + '/content/items/' + item_id,
            params={
                'token': self.token,
                'f': 'json'
            }
        )
        return FeatureLayer(
            item_data['url'] + '/' + str(layer_number),
            self
        )

    @property
    def token(self):
        '''GIS access token'''
        self._get_token()
        return self._token


class AgolGIS(_GIS):
    '''Connection to ArcGIS Online'''
    def __init__(self, username, password, url='https://www.arcgis.com'):
        super().__init__(url)
        self.username = username
        self.password = password

    def _get_token(self):
        if not self._token or \
            datetime.datetime.utcnow() > self.token_expiration - datetime.timedelta(minutes=2):
            token_data = url_post(
                self.rest_url + '/generateToken',
                data={
                    'username': self.username,
                    'password': self.password,
                    'referer': self.url,
                    'f': 'json'
                }
            )
            self._token = token_data['token']
            self.token_expiration = datetime.datetime.utcfromtimestamp(token_data['expires'] / 1000)


class PortalGIS(_GIS):
    '''Connection to ArcGIS Enterprise Portal'''
    def __init__(self, url, client_id, refresh_token):
        super().__init__(url)
        self.client_id = client_id
        self.refresh_token = refresh_token
        self.username = None

    def _get_token(self):
        if not self._token or \
            datetime.datetime.utcnow() > self.token_expiration - datetime.timedelta(minutes=2):
            token_data = url_get(
                self.rest_url + '/oauth2/token',
                params={
                    'grant_type': 'refresh_token',
                    'client_id': self.client_id,
                    'refresh_token': self.refresh_token,
                    'f': 'json'
                }
            )
            self._token = token_data['access_token']
            self.token_expiration = datetime.datetime.utcnow() + datetime.timedelta(seconds=token_data['expires_in'])
            self.username = token_data['username']
