import datetime
from urllib.parse import urljoin
import requests


class PortalGIS:
    '''Connection to an ArcGIS Enterprise Portal'''
    def __init__(self, url, client_id, refresh_token) -> None:
        self.url = url
        self._rest_url = urljoin(url, 'sharing/rest')
        self._client_id = client_id
        self._refresh_token = refresh_token
        self._token = None
        self._token_expiration = None

    def _get_token(self):
        if not self._token or \
            datetime.datetime.now() - self._token_expiration > datetime.timedelta(minutes=28):
            token_data = requests.get(
                urljoin(self._rest_url, 'oauth2/token'),
                params={
                    'grant_type': 'refresh_token',
                    'client_id': self._client_id,
                    'refresh_token': self._refresh_token
                }
            ).json()
            self._token = token_data['access_token']
            self._token_expiration = datetime.datetime.now() + datetime.timedelta(seconds=token_data['expires_in'])

    @property
    def token(self):
        '''GIS access token'''
        self._get_token()
        return self._token
