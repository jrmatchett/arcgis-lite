import requests
from gis import PortalGIS


class FeatureLayer:
    '''ArcGIS Feature Layer'''
    def __init__(self, url: str, gis: PortalGIS=None) -> None:
        self.url = url
        self.gis = gis

    def query(self, where: str='1=1', outFields: str='*', returnGeometry: bool=True, outSR: int=4326) -> list:
        '''Query features'''
        query_params = {k: v for k,v in locals().items() if k != 'self'}
        query_params['f'] = 'json'
        query_params['token'] = self.gis.token if self.gis else None
        return self._paged_query(query_params, [])

    def _paged_query(self, query_params, features):
        query_params['resultOffset'] = len(features)
        print(f"query rec start: {query_params['resultOffset']}", flush=True)
        query_data = requests.get(
            self.url + '/query',
            params=query_params
        ).json()
        features.extend(query_data['features'])
        if 'exceededTransferLimit' in query_data and query_data['exceededTransferLimit']:
            self._paged_query(query_params, features)
        return features
