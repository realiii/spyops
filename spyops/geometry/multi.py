# -*- coding: utf-8 -*-
"""
Build Multi Geometry
"""

from fudgeo import FeatureClass
from fudgeo.enumeration import ShapeType
from numpy import ndarray
from shapely import MultiLineString, MultiPoint, MultiPolygon, force_2d
from shapely.constructive import normalize
from shapely.creation import prepare
from shapely.ops import unary_union

from spyops.geometry.validate import (
    _check_geometries, _get_validated_geoms, check_linestring, check_point,
    check_polygon)


def build_multi(features: FeatureClass | ndarray | list | None) \
        -> MultiPoint | MultiLineString | MultiPolygon | None:
    """
    Build MultiPoint, MultiLineString or MultiPolygon from a Feature Class or
    collection of geometries.
    """
    if not len(features):
        return None
    if isinstance(features, FeatureClass):
        shape_type = features.shape_type
    else:
        shape_type = features[0].geom_type.upper()
        features = force_2d(features)
    if shape_type in (ShapeType.point, ShapeType.multi_point):
        return _multi_point(features)
    elif shape_type in (ShapeType.linestring, ShapeType.multi_linestring):
        return _multi_linestring(features)
    elif shape_type in (ShapeType.polygon, ShapeType.multi_polygon):
        return _multi_polygon(features)
    else:
        raise ValueError(f'Unsupported shape type: {shape_type}')
# End build_multi function


def _multi_polygon(features: FeatureClass | ndarray) -> MultiPolygon:
    """
    Build MultiPolygon from Polygon or MultiPolygon Feature Class or Geometries
    """
    geoms = []
    checker = check_polygon
    if isinstance(features, FeatureClass):
        geoms = _get_validated_geoms(features, checker=checker)
    else:
        _check_geometries(features, checker=checker, geoms=geoms)
    if not geoms:
        return MultiPolygon()
    multi = unary_union(normalize(geoms)).normalize()
    prepare(multi)
    # noinspection PyTypeChecker
    return multi
# End _multi_polygon function


def _multi_linestring(features: FeatureClass | ndarray) -> MultiLineString:
    """
    Build MultiLineString from LineString or MultiLineString Feature Class
    or Geometries
    """
    geoms = []
    checker = check_linestring
    if isinstance(features, FeatureClass):
        geoms = _get_validated_geoms(features, checker=checker)
    else:
        _check_geometries(features, checker=checker, geoms=geoms)
    multi = MultiLineString(geoms)
    prepare(multi)
    return multi
# End _multi_linestring function


def _multi_point(features: FeatureClass | ndarray) -> MultiPoint:
    """
    Build MultiPoint from Point or MultiPoint Feature Class
    """
    geoms = []
    checker = check_point
    if isinstance(features, FeatureClass):
        geoms = _get_validated_geoms(features, checker=checker)
    else:
        _check_geometries(features, checker=checker, geoms=geoms)
    multi = MultiPoint(geoms)
    prepare(multi)
    return multi
# End _multi_point function


if __name__ == '__main__':  # pragma: no cover
    pass
