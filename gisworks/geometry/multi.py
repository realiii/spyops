# -*- coding: utf-8 -*-
"""
Build Multi Geometry
"""


from typing import Callable, Optional, TYPE_CHECKING

from fudgeo.constant import FETCH_SIZE
from fudgeo.enumeration import GeometryType
from shapely import MultiLineString, MultiPoint, MultiPolygon
from shapely.constructive import normalize
from shapely.creation import prepare
from shapely.ops import unary_union

from gisworks.geometry.enumeration import DimensionOption
from gisworks.geometry.util import get_geoms_iter, to_shapely
from gisworks.geometry.validate import (
    check_linestring, check_point, check_polygon)


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass
    from shapely import MultiLineString, MultiPoint, MultiPolygon


def build_multi(feature_class: Optional['FeatureClass']) \
        -> MultiPoint | MultiLineString | MultiPolygon | None:
    """
    Build MultiPoint, MultiLine or MultiPolygon
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


def _get_validated_geoms(feature_class: 'FeatureClass',
                         checker: Callable) -> list:
    """
    Get Shapely Geometries from Feature Class, forcing to 2D.
    """
    geoms = []
    cursor = feature_class.select()
    while features := cursor.fetchmany(FETCH_SIZE):
        geometries = to_shapely(features, option=DimensionOption.TWO_D)
        for geometry in geometries:
            for geom in get_geoms_iter(geometry):
                if checker(geom) is None:
                    continue
                geoms.append(geom)
    return geoms
# End _get_validated_geoms function


def _build_multi_polygon(feature_class: 'FeatureClass') -> MultiPolygon:
    """
    Build MultiPolygon from Polygon or MultiPolygon Feature Class
    """
    geoms = _get_validated_geoms(feature_class, checker=check_polygon)
    if not geoms:
        return MultiPolygon()
    multi = unary_union(normalize(geoms)).normalize()
    prepare(multi)
    # noinspection PyTypeChecker
    return multi
# End _build_multi_polygon function


def _build_multi_linestring(feature_class: 'FeatureClass') -> MultiLineString:
    """
    Build MultiLineString from LineString or MultiLineString Feature Class
    """
    geoms = _get_validated_geoms(feature_class, checker=check_linestring)
    if not geoms:
        return MultiLineString()
    multi = MultiLineString(geoms)
    prepare(multi)
    return multi
# End _build_multi_linestring function


def _build_multi_point(feature_class: 'FeatureClass') -> MultiPoint:
    """
    Build MultiPoint from Point or MultiPoint Feature Class
    """
    geoms = _get_validated_geoms(feature_class, checker=check_point)
    if not geoms:
        return MultiPoint()
    multi = MultiPoint(geoms)
    prepare(multi)
    return multi
# End _build_multi_point function


if __name__ == '__main__':  # pragma: no cover
    pass
