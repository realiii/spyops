# -*- coding: utf-8 -*-
"""
Build Multi Geometry
"""


from typing import Callable

from fudgeo import FeatureClass
from fudgeo.constant import FETCH_SIZE
from fudgeo.enumeration import GeometryType
from shapely import (
    LineString, MultiLineString, MultiPoint, MultiPolygon, Point, Polygon,
    from_wkb, prepare)
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from gisworks.shared.constant import LINES_ATTR, POINTS_ATTR, POLYGONS_ATTR
from gisworks.shared.field import get_geometry_column_name
from gisworks.geometry.validate import (
    check_linestring, check_point,
    check_polygon)


def build_multi(feature_class: FeatureClass | None) \
        -> MultiPoint | MultiLineString | MultiPolygon | None:
    """
    Build Multi Point, Multi Line or Multi Polygon
    """
    if not feature_class:
        return None
    shape_type = feature_class.shape_type
    if shape_type in (GeometryType.point, GeometryType.multi_point):
        return _build_multi_point(feature_class)
    elif shape_type in (GeometryType.linestring, GeometryType.multi_linestring):
        return _build_multi_linestring(feature_class)
    elif shape_type in (GeometryType.polygon, GeometryType.multi_polygon):
        return _build_multi_polygon(feature_class)
    else:
        raise ValueError(f'Unsupported shape type: {shape_type}')
# End build_multi function


def _get_geoms(feature_class: FeatureClass, attr: str,
               checker: Callable[[BaseGeometry], BaseGeometry | None]) \
        -> list[Point] | list[LineString] | list[Polygon]:
    """
    Get Shapely Geometries from Feature Class
    """
    geoms = []
    column_name = get_geometry_column_name(
        feature_class, include_geom_type=True)
    with feature_class.geopackage.connection as cin:
        cursor = cin.execute(
            f"""SELECT {column_name} 
                FROM {feature_class.escaped_name}""")
        while geometries := cursor.fetchmany(FETCH_SIZE):
            for geometry, in geometries:
                for geom in getattr(geometry, attr, [geometry]):
                    g = from_wkb(geom.wkb)
                    if checker(g) is None:
                        continue
                    geoms.append(g)
    return geoms
# End _get_geoms function


def _build_multi_polygon(feature_class: FeatureClass) -> MultiPolygon:
    """
    Build MultiPolygon from Polygon or MultiPolygon Feature Class
    """
    # noinspection PyTypeChecker
    geoms = _get_geoms(feature_class, attr=POLYGONS_ATTR, checker=check_polygon)
    if not geoms:
        return MultiPolygon()
    multi = unary_union(geoms)
    prepare(multi)
    # noinspection PyTypeChecker
    return multi
# End _build_multi_polygon function


def _build_multi_linestring(feature_class: FeatureClass) -> MultiLineString:
    """
    Build MultiLineString from LineString or MultiLineString Feature Class
    """
    # noinspection PyTypeChecker
    geoms = _get_geoms(feature_class, attr=LINES_ATTR, checker=check_linestring)
    multi = MultiLineString(geoms)
    prepare(multi)
    # noinspection PyTypeChecker
    return multi
# End _build_multi_linestring function


def _build_multi_point(feature_class: FeatureClass) -> MultiPoint:
    """
    Build MultiPoint from Point or MultiPoint Feature Class
    """
    # noinspection PyTypeChecker
    geoms = _get_geoms(feature_class, attr=POINTS_ATTR, checker=check_point)
    multi = MultiPoint(geoms)
    prepare(multi)
    # noinspection PyTypeChecker
    return multi
# End _build_multi_point function


if __name__ == '__main__':  # pragma: no cover
    pass
