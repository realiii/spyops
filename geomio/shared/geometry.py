# -*- coding: utf-8 -*-
"""
Geometry Functionality
"""


from math import nan
from typing import Any

from fudgeo import FeatureClass
from fudgeo.constant import FETCH_SIZE
from fudgeo.enumeration import GeometryType
from fudgeo.geometry import (
    LineString, LineStringM, LineStringZ, LineStringZM, MultiLineString,
    MultiLineStringM, MultiLineStringZ, MultiLineStringZM, MultiPoint,
    MultiPointM, MultiPointZ, MultiPointZM, MultiPolygon, MultiPolygonM,
    MultiPolygonZ, MultiPolygonZM, Point, PointM, PointZ, PointZM, Polygon,
    PolygonM, PolygonZ, PolygonZM)
from fudgeo.util import get_extent
from numpy import isfinite
from shapely import (
    LineString as ShapelyLineString, MultiLineString as ShapelyMultiLineString,
    MultiPoint as ShapelyMultiPoint, MultiPolygon as ShapelyMultiPolygon,
    Point as ShapelyPoint, Polygon as ShapelyPolygon, make_valid, prepare)
from shapely.io import from_wkb
from shapely.ops import unary_union

from geomio.shared.base import OverlayConfig
from geomio.shared.constant import GEOMS_ATTR
from geomio.shared.exception import OperationsError
from geomio.shared.field import get_geometry_column_name
from geomio.shared.hint import EXTENT

SHAPELY_GEOMETRY_LOOKUP: dict[str, tuple[Any, Any]] = {
    GeometryType.point: (ShapelyPoint, ShapelyMultiPoint),
    GeometryType.multi_point: (ShapelyPoint, ShapelyMultiPoint),
    GeometryType.linestring: (ShapelyLineString, ShapelyMultiLineString),
    GeometryType.multi_linestring: (ShapelyLineString, ShapelyMultiLineString),
    GeometryType.polygon: (ShapelyPolygon, ShapelyMultiPolygon),
    GeometryType.multi_polygon: (ShapelyPolygon, ShapelyMultiPolygon),
}


FUDGEO_GEOMETRY_LOOKUP: dict[str, dict[tuple[bool, bool], Any]] = {
    GeometryType.point: {
        (False, False): Point,
        (True, False): PointZ,
        (False, True): PointM,
        (True, True): PointZM},
    GeometryType.multi_point: {
        (False, False): MultiPoint,
        (True, False): MultiPointZ,
        (False, True): MultiPointM,
        (True, True): MultiPointZM},
    GeometryType.linestring: {
        (False, False): LineString,
        (True, False): LineStringZ,
        (False, True): LineStringM,
        (True, True): LineStringZM},
    GeometryType.multi_linestring: {
        (False, False): MultiLineString,
        (True, False): MultiLineStringZ,
        (False, True): MultiLineStringM,
        (True, True): MultiLineStringZM},
    GeometryType.polygon: {
        (False, False): Polygon,
        (True, False): PolygonZ,
        (False, True): PolygonM,
        (True, True): PolygonZM},
    GeometryType.multi_polygon: {
        (False, False): MultiPolygon,
        (True, False): MultiPolygonZ,
        (False, True): MultiPolygonM,
        (True, True): MultiPolygonZM}
}


def build_multi_polygon(feature_class: FeatureClass) -> ShapelyMultiPolygon:
    """
    Build MultiPolygon from Polygon or MultiPolygon Feature Class
    """
    polygons = []
    column_name = get_geometry_column_name(
        feature_class, include_geom_type=True)
    is_multi = feature_class.is_multi_part
    with feature_class.geopackage.connection as conn:
        cursor = conn.execute(
            f"""SELECT {column_name} 
                FROM {feature_class.escaped_name}""")
        while geoms := cursor.fetchmany(FETCH_SIZE):
            for geom, in geoms:
                polys = geom.polygons if is_multi else [geom]
                for poly in polys:
                    # noinspection PyTypeChecker
                    polygon: ShapelyPolygon = from_wkb(poly.wkb)
                    if check_polygon(polygon) is None:  # pragma: no cover
                        continue
                    polygons.append(polygon)
    # noinspection PyTypeChecker
    multi: ShapelyMultiPolygon = unary_union(polygons)
    prepare(multi)
    return multi
# End build_multi_polygon function


def check_polygon(polygon: ShapelyPolygon | ShapelyMultiPolygon) \
        -> ShapelyMultiPolygon | ShapelyPolygon | None:
    """
    Check Polygon
    """
    if polygon.is_valid:
        return polygon
    polygon = make_valid(polygon, method='structure')
    if not polygon.is_valid:
        return None
    polygons = [p for p in getattr(polygon, GEOMS_ATTR, [polygon])
                if p.is_valid and isinstance(p, ShapelyPolygon)]
    if not polygons:
        return None
    if len(polygons) == 1:
        return polygons[0]
    return ShapelyMultiPolygon(polygons)
# End check_polygon function


def overlay_config(source: FeatureClass, target: FeatureClass,
                   operator: FeatureClass) -> OverlayConfig:
    """
    Overlay Configuration
    """
    polygon = build_multi_polygon(operator)
    geom_type = source.geometry_type.upper()
    is_multi = source.is_multi_part
    cls = FUDGEO_GEOMETRY_LOOKUP[geom_type][source.has_z, source.has_m]
    shapely_types = _, multi_cls = SHAPELY_GEOMETRY_LOOKUP.get(geom_type)
    return OverlayConfig(
        fudgeo_cls=cls, is_multi=is_multi, shapely_multi_cls=multi_cls,
        geometry=polygon, shapely_types=shapely_types,
        srs_id=target.spatial_reference_system.srs_id)
# End overlay_config function


def set_extent(feature_class: FeatureClass) -> None:
    """
    Set Extent on a Feature Class using existing, spatial index, or
    geometry extents.
    """
    try:
        feature_class.extent = extent_from_feature_class(feature_class)
    except OperationsError:  # pragma: no cover
        return
# End set_extent function


def _extent_from_index_or_geometry(feature_class: FeatureClass) -> EXTENT:
    """
    Get the Extent from the Spatial Index, fail over to the extent derived
    from geometries.
    """
    extent = _extent_from_spatial_index(feature_class)
    if isfinite(extent).all():
        return extent
    else:  # pragma: no cover
        return get_extent(feature_class)
# End _extent_from_index_or_geometry function


def extent_from_feature_class(feature_class: FeatureClass) -> EXTENT:
    """
    Returns the extent from a feature class, use the extent if it has
    been set, if not check the spatial index extent, failing over to
    brute force check of all features.
    """
    extent = feature_class.extent
    if isfinite(extent).all():
        return extent
    extent = _extent_from_index_or_geometry(feature_class)
    if isfinite(extent).all():
        return extent
    else:  # pragma: no cover
        raise OperationsError(
            f'{feature_class.name} is empty or only contains empty geometries')
# End extent_from_feature_class function


def _extent_from_spatial_index(feature_class: FeatureClass) -> EXTENT:
    """
    Extent from Spatial Index
    """
    empty = nan, nan, nan, nan
    if not feature_class.has_spatial_index:  # pragma: no cover
        return empty
    cursor = feature_class.geopackage.connection.execute(f"""
        SELECT MIN(minx) AS MIN_X, MIN(miny) AS MIN_Y, 
               MAX(maxx) AS MAX_X, MAX(maxy) AS MAX_Y
        FROM {feature_class.spatial_index_name}""")
    extent = cursor.fetchone()
    if not extent:  # pragma: no cover
        return empty
    if None in extent:  # pragma: no cover
        return empty
    return extent
# End _extent_from_spatial_index function


if __name__ == '__main__':  # pragma: no cover
    pass
