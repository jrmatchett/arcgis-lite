import datetime
import requests


class PortalGIS:
    '''Connection to an ArcGIS Enterprise Portal'''
    def __init__(self, url: str, client_id: str, refresh_token: str) -> None:
        self.url = url.strip('/')
        self.rest_url = url + '/sharing/rest'
        self.client_id = client_id
        self.refresh_token = refresh_token
        self._token = None
        self.token_expiration = None

    def _get_token(self) -> None:
        if not self._token or \
            datetime.datetime.now() - self.token_expiration > datetime.timedelta(minutes=28):
            token_data = requests.get(
                self.rest_url + '/oauth2/token',
                params={
                    'grant_type': 'refresh_token',
                    'client_id': self.client_id,
                    'refresh_token': self.refresh_token
                }
            ).json()
            self._token = token_data['access_token']
            self.token_expiration = datetime.datetime.now() + datetime.timedelta(seconds=token_data['expires_in'])

    @property
    def token(self) -> str:
        '''GIS access token'''
        self._get_token()
        return self._token
