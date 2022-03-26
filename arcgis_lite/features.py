from . import _requests


__all__ = ['FeatureLayer', 'FeatureSet']


class FeatureLayer:
    '''ArcGIS Hosted Feature Layer'''
    def __init__(self, url, gis=None):
        self.url = url.strip('/')
        self.gis = gis
        self._properties = None

    def __repr__(self):
        return f"FeatureLayer @ {self.url}"

    def query(self, where='1=1', outFields='*', returnGeometry=True, **kwargs):
        '''Query features'''
        query_params = {
            'where': where,
            'outFields': outFields,
            'returnGeometry': returnGeometry,
            'f': 'json',
            'token': self.token
        }
        query_params.update(kwargs)
        return self._paged_query(query_params, [])

    def _paged_query(self, query_params, features):
        query_params['resultOffset'] = len(features)
        query_data = _requests.get(
            self.url + '/query',
            params=query_params
        )
        if not 'features' in query_data:
            return query_data, None
        features.extend(query_data['features'])
        if 'exceededTransferLimit' in query_data and query_data['exceededTransferLimit']:
            self._paged_query(query_params, features)
        return FeatureSet(query_data, features)

    def add_features(self, features):
        '''Add features'''
        add_result = _requests.post(
            self.url + '/addFeatures',
            data={
                'features': features,
                'f': 'json',
                'token': self.token
            }
        )
        return add_result

    def update_features(self, features):
        '''Update features'''
        update_result = _requests.post(
            self.url + '/updateFeatures',
            data={
                'features': features,
                'f': 'json',
                'token': self.token
            }
        )
        return update_result

    def delete_features(self, where=None, objectIds=None):
        '''Delete features'''
        delete_result = _requests.post(
            self.url + '/deleteFeatures',
            data={
                'where': where,
                'objectIds': objectIds,
                'f': 'json',
                'token': self.token
            }
        )
        return delete_result

    def truncate_features(self, attachmentOnly=False, asynchronous=False):
        '''Truncate (delete all) features'''
        admin_url = self.url.replace('rest/services', 'rest/admin/services')
        truncate_result = _requests.post(
            admin_url + '/truncate',
            data={
                'attachmentOnly': attachmentOnly,
                'async': asynchronous,
                'f': 'json',
                'token': self.token
            }
        )
        return truncate_result

    @property
    def token(self):
        return self.gis.token if self.gis else ''

    @property
    def properties(self):
        if not self._properties:
            self._properties = _requests.get(self.url, {'f': 'json', 'token': self.token})
        return self._properties


class FeatureSet:
    '''ArcGIS Feature Set'''
    def __init__(self, query_data, features):
        property_keys = ['fields', 'geometryType', 'spatialReference']
        self.properties = {k:v for k,v in query_data.items() if k in property_keys}
        if features and 'geometryType' in self.properties and not 'geometry' in features[0]:
            del self.properties['geometryType']
        self.features = features

    def __repr__(self):
        if 'geometryType' in self.properties:
            geom_type = self.properties['geometryType'].replace('esriGeometry', '').lower()
        else:
            geom_type = 'non-spatial'
        n_features = len(self.features)
        return f"FeatureSet with {n_features} {geom_type} feature{'s' if n_features != 1 else ''}"

    def geodataframe(self, decode_domains=True, use_aliases=False):
        """Returns a feature set's data as a GeoPandas GeoDataFrame, decoding any domain values by
        default and optionally using field aliases for the dataframe column names.
        Arguments:
        decode_domains  If True, replaces domain codes with their values.
        use_aliases     If True, uses field aliases for the dataframe column names.
        """
        gdf = self.gdf
        fields = self.properties['fields']
        if decode_domains:
            gdf_columns = gdf.columns
            for f in fields:
                if ('domain' in f) and (f['domain'] is not None) and (f['name'] in gdf_columns):
                    code_values = {k:v for k,v in [(d['code'], d['name']) for d in f['domain']['codedValues']]}
                    gdf[f['name']].replace(code_values, inplace=True)
        if use_aliases:
            field_aliases = {k:v for k,v in [(f['name'], f['alias']) for f in fields]}
            gdf.rename(columns=field_aliases, inplace=True)
        return gdf

    @property
    def gdf(self):
        '''Get a GeoPandas GeoDataFrame'''
        from ._geodata import to_geodataframe
        return to_geodataframe(self, fix_polygons=True)
