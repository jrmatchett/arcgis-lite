import json
from url_requests import url_get, url_post


class FeatureLayer:
    '''ArcGIS Feature Layer'''
    def __init__(self, url, gis=None):
        self.url = url
        self.gis = gis

    def query(self, where='1=1', outFields='*', returnGeometry=True, **kwargs):
        '''Query features'''
        query_params = {k:v for k,v in locals().items() if k not in ['self', 'kwargs']}
        if kwargs:
            query_params.update(kwargs)
        query_params['f'] = 'json'
        query_params['token'] = self.token
        #print(query_params, flush=True)
        return self._paged_query(query_params, [])

    def _paged_query(self, query_params, features):
        query_params['resultOffset'] = len(features)
        #print(f"query rec start: {query_params['resultOffset']}", flush=True)
        query_data = url_get(
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
        add_result = url_post(
            self.url + '/addFeatures',
            data={
                'features': json.dumps(features),
                'f': 'json',
                'token': self.token
            }
        )
        return add_result

    def update_features(self, features):
        update_result = url_post(
            self.url + '/updateFeatures',
            data={
                'features': json.dumps(features),
                'f': 'json',
                'token': self.token
            }
        )
        return update_result

    def delete_features(self, where=None, objectIds=None):
        delete_result = url_post(
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
