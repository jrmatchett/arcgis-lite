import geopandas as gpd
from shapely.geometry import Point, MultiPoint, LinearRing, Polygon,\
    MultiPolygon, LineString, MultiLineString
from shapely.validation import explain_validity
import warnings


__all__ = ['to_arcgis_geometry']


def to_GeoDataFrame(feature_set, fix_polygons):
    # construct GeoSeries
    if not 'geometry' in feature_set.features[0]:
        geoseries = None
    elif feature_set.properties['geometryType'] == 'esriGeometryPoint':
        geoseries = gpd.GeoSeries(
            [Point(f['geometry']['x'], f['geometry']['y']) for f in feature_set.features]
        )
    elif feature_set.properties['geometryType'] == 'esriGeometryPolyline':
        geoseries = gpd.GeoSeries(
            [to_shapely_line(f['geometry']) for f in feature_set.features]
        )
    elif feature_set.properties['geometryType'] == 'esriGeometryPolygon':
        geoseries = gpd.GeoSeries(
            [to_shapely_polygon(f['geometry'], fix_polygons) for f in feature_set.features]
        )
    else:
        raise NotImplementedError
    # construct GeoDataFrame
    geodataframe = gpd.GeoDataFrame(
        data=[f['attributes'] for f in feature_set.features],
        geometry=geoseries,
        crs=f"EPSG:{feature_set.properties['spatialReference']['wkid']}" \
            if 'spatialReference' in feature_set.properties and geoseries is not None\
            else None
    )
    # convert datetime fields
    datetime_fields = [f['name'] for f in feature_set.properties['fields'] if f['type'] == 'esriFieldTypeDate']
    for field in datetime_fields:
        geodataframe[field] = gpd.pd.to_datetime(geodataframe[field], unit='ms')
    return geodataframe


def to_shapely_line(arcgis_polyline):
    paths = arcgis_polyline['paths']
    return LineString(paths) if len(paths) == 1 else MultiLineString(paths)


def to_shapely_polygon(arcgis_polygon, fix_polygons):
    # extract exterior and interior rings
    exterior_rings, interior_rings = [], []
    for ring in map(LinearRing, arcgis_polygon['rings']):
        interior_rings.append(ring) if ring.is_ccw else exterior_rings.append(ring)

    # create polygons for each exterior ring
    polys = []
    for exterior_ring in exterior_rings:
        exterior_poly = Polygon(exterior_ring)
        if len(interior_rings) > 0:
            # determine which interior rings are within the exterior ring
            within_rings, outside_rings = [], []
            for interior_ring in interior_rings:
                within_rings.append(interior_ring)\
                    if Polygon(interior_ring).intersects(exterior_poly)\
                    else outside_rings.append(interior_ring)
            polys.append(Polygon(exterior_ring, within_rings))
            interior_rings = outside_rings
        else:
            polys.append(exterior_poly)

    if len(polys) == 1:
        poly_shp = Polygon(polys[0])
    else:
        poly_shp = MultiPolygon(polys)

    # check validity and fix any self-intersecting rings
    if not poly_shp.is_valid:
        invalid_reason = explain_validity(poly_shp)
        invalid_message = 'Polygon is not valid ({})'.format(invalid_reason)
        if 'Self-intersection' in invalid_reason and fix_polygons:
            # fix with buffer trick
            poly_shp = poly_shp.buffer(0.0)
            invalid_message += '; self-intersections were automatically fixed'
            invalid_message += '.'
            warnings.simplefilter('always', UserWarning)
            warnings.warn(invalid_message)

    return poly_shp


def tuples_to_lists(tuples):
    return list(map(tuples_to_lists, tuples)) if isinstance(tuples, (list, tuple)) else tuples


def to_arcgis_geometry(geometry, spatial_reference):
    """Return an arcgis Geometry.

    Arguments:
    spatial_reference  A spatial reference integer code or definition
                       dictionary, for example {'wkid': 3857}
    """

    if isinstance(spatial_reference, int):
        spatial_reference = {'wkid': spatial_reference}

    if isinstance(geometry, Point):
        geom = {'x': geometry.x, 'y': geometry.y}

    elif isinstance(geometry, MultiPoint):
        geom = {'points': tuples_to_lists(geometry.__geo_interface__['coordinates'])}

    elif isinstance(geometry, LineString):
        geom = {'paths': [tuples_to_lists(geometry.__geo_interface__['coordinates'])]}

    elif isinstance(geometry, MultiLineString):
        geom = {'paths': tuples_to_lists(geometry.__geo_interface__['coordinates'])}

    elif isinstance(geometry, Polygon):
        linear_rings = [geometry.exterior]
        linear_rings += geometry.interiors
        rings = [tuples_to_lists(r.__geo_interface__['coordinates']) for r in linear_rings]
        geom = {'rings': rings}

    elif isinstance(geometry, MultiPolygon):
        linear_rings = []
        for poly in geometry.geoms:
            linear_rings += [poly.exterior]
            linear_rings += poly.interiors
        rings = [tuples_to_lists(r.__geo_interface__['coordinates']) for r in linear_rings]
        geom = {'rings': rings}

    geom['spatialReference'] = spatial_reference
    return geom
