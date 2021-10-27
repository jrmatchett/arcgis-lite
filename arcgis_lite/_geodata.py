import geopandas as gpd
from shapely.geometry import Point, LinearRing, Polygon, MultiPolygon, LineString, MultiLineString
from shapely.validation import explain_validity
import warnings


def to_GeoDataFrame(feature_set):
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
        geoseries = [to_shapely_polygon(f['geometry']) for f in feature_set.features]
    else:
        raise NotImplementedError
    # construct GeoDataFrame
    return gpd.GeoDataFrame(
        data=[f['attributes'] for f in feature_set.features],
        geometry=geoseries,
        crs=f"EPSG:{feature_set.properties['spatialReference']['wkid']}" \
            if 'spatialReference' in feature_set.properties \
            else None
    )


def to_shapely_line(arcgis_polyline):
    paths = arcgis_polyline['paths']
    return LineString(paths) if len(paths) == 1 else MultiLineString(paths)


def to_shapely_polygon(arcgis_polygon, fix_self_intersections=True, warn_invalid=True):
    """Return a Shapely [Mulit]Polygon.

    Alternative to arcgis as_shapely which handles polygons with holes and fixes
    self-intersecting rings (as_shapely may not work properly when the python
    environment does not have ArcPy available).

    Arguments:
    fix_self_intersections  Fix self-intersecting polygons.
    warn_invalid            Issue a warning if polygon is invalid.
    """
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
        if 'Self-intersection' in invalid_reason and fix_self_intersections:
            # fix with buffer trick
            poly_shp = poly_shp.buffer(0.0)
            invalid_message += '; self-intersections were automatically fixed'
        if warn_invalid:
            invalid_message += '.'
            warnings.simplefilter('always', UserWarning)
            warnings.warn(invalid_message)

    return poly_shp
