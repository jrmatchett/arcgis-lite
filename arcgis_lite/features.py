import json
from . import requests


__all__ = ['FeatureLayer']


class FeatureLayer:
    '''ArcGIS Hosted Feature Layer'''
    def __init__(self, url, gis=None):
        self.url = url.strip('/')
        self.gis = gis

    def query(self, where='1=1', outFields='*', returnGeometry=True, **kwargs):
        '''Query features'''
        query_params = {'where': where, 'outFields': outFields, 'returnGeometry': returnGeometry}
        query_params['f'] = 'json'
        query_params['token'] = self.token
        if kwargs:
            query_params.update(kwargs)
        return self._paged_query(query_params, [])

    def _paged_query(self, query_params, features):
        query_params['resultOffset'] = len(features)
        query_data = requests.get(
            self.url + '/query',
            params=query_params
        )
        if not 'features' in query_data:
            return query_data
        features.extend(query_data['features'])
        if 'exceededTransferLimit' in query_data and query_data['exceededTransferLimit']:
            self._paged_query(query_params, features)
        return features

    def add_features(self, features):
        '''Add features'''
        add_result = requests.post(
            self.url + '/addFeatures',
            data={
                'features': json.dumps(features),
                'f': 'json',
                'token': self.token
            }
        )
        return add_result

    def update_features(self, features):
        '''Update features'''
        update_result = requests.post(
            self.url + '/updateFeatures',
            data={
                'features': json.dumps(features),
                'f': 'json',
                'token': self.token
            }
        )
        return update_result

    def delete_features(self, where=None, objectIds=None):
        '''Delete features'''
        delete_result = requests.post(
            self.url + '/deleteFeatures',
            data={
                'where': where,
                'objectIds': objectIds,
                'f': 'json',
                'token': self.token
            }
        )
        return delete_result

    @property
    def token(self):
        return self.gis.token if self.gis else None

    @property
    def properties(self):
        return requests.get(self.url, {'f': 'json', 'token': self.token})
