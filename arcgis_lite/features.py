import json
import requests_lite


class FeatureLayer:
    '''ArcGIS Feature Layer'''
    def __init__(self, url, gis=None):
        self.url = url
        self.gis = gis

    def query(self, where='1=1', outFields='*', returnGeometry=True, **kwargs):
        '''Query features'''
        query_params = {'where': where, 'outFields': outFields, 'returnGeometry': returnGeometry}
        query_params['f'] = 'json'
        query_params['token'] = self.token
        if kwargs:
            query_params.update(kwargs)
        #print(query_params, flush=True)
        return self._paged_query(query_params, [])

    def _paged_query(self, query_params, features):
        query_params['resultOffset'] = len(features)
        #print(f"query rec start: {query_params['resultOffset']}", flush=True)
        query_data = requests_lite.get(
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
        add_result = requests_lite.post(
            self.url + '/addFeatures',
            data={
                'features': json.dumps(features),
                'f': 'json',
                'token': self.token
            }
        )
        return add_result

    def update_features(self, features):
        update_result = requests_lite.post(
            self.url + '/updateFeatures',
            data={
                'features': json.dumps(features),
                'f': 'json',
                'token': self.token
            }
        )
        return update_result

    def delete_features(self, where=None, objectIds=None):
        delete_result = requests_lite.post(
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
    #print(query_params, flush=True)
    geocode_result = requests_lite.get(
        'https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates',
        query_params
    )
    return geocode_result
