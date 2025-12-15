# -*- coding: utf-8 -*-
"""
Geometry Functionality
"""


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
from shapely import (
    LineString as ShapelyLineString, MultiLineString as ShapelyMultiLineString,
    MultiPoint as ShapelyMultiPoint, MultiPolygon as ShapelyMultiPolygon,
    Point as ShapelyPoint, Polygon as ShapelyPolygon, make_valid, prepare)
from shapely.io import from_wkb
from shapely.ops import unary_union

from geomio.shared.constants import GEOMS_ATTR
from geomio.shared.field import get_geometry_column_name
from geomio.shared.types import OverlayConfig

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
                    if check_polygon(polygon) is None:
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
                if p.is_valid and isinstance(polygon, ShapelyPolygon)]
    if not polygons:
        return None
    if len(polygons) == 1:
        return polygons[0]
    return ShapelyMultiPolygon(polygons)
# End check_polygon function


def overlay_config(source: FeatureClass, operator: FeatureClass) -> OverlayConfig:
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
        geometry=polygon, shapely_types=shapely_types)
# End overlay_config function


if __name__ == '__main__':  # pragma: no cover
    pass
