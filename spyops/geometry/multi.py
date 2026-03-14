# -*- coding: utf-8 -*-
"""
Build Multi Geometry
"""


from typing import Callable

from fudgeo import FeatureClass
from fudgeo.enumeration import ShapeType
from numpy import asarray, ndarray
from shapely import MultiLineString, MultiPoint, MultiPolygon, force_2d
from shapely.constructive import normalize
from shapely.creation import prepare
from shapely.set_operations import union_all

from spyops.geometry.util import get_geoms_iter, get_validity
from spyops.geometry.validate import (
    _check_geometries, _get_validated_geoms, check_linestring, check_point,
    check_polygon)
from spyops.shared.hint import GRID_SIZE
from spyops.shared.keywords import GEOMS_ATTR


def build_multi(features: FeatureClass | ndarray | None, select_sql: str | None,
                transformer: Callable | None) \
        -> MultiPoint | MultiLineString | MultiPolygon | None:
    """
    Build MultiPoint, MultiLineString, or MultiPolygon from a Feature Class or
    collection of geometries.
    """
    if not len(features):
        return None
    if isinstance(features, FeatureClass):
        shape_type = features.shape_type
    else:
        shape_type = features[0].geom_type.upper()
        features = force_2d(features)
        if transformer:
            features = transformer(features)
            features = features[get_validity(features, transformer=transformer)]
    if shape_type in (ShapeType.point, ShapeType.multi_point):
        return _multi_point(
            features, select_sql=select_sql, transformer=transformer)
    elif shape_type in (ShapeType.linestring, ShapeType.multi_linestring):
        return _multi_linestring(
            features, select_sql=select_sql, transformer=transformer)
    elif shape_type in (ShapeType.polygon, ShapeType.multi_polygon):
        return _multi_polygon(
            features, select_sql=select_sql, transformer=transformer)
    else:  # pragma: no cover
        raise ValueError(f'Unsupported shape type: {shape_type}')
# End build_multi function


def build_dissolved(geometries: ndarray, shape_type: str,
                    grid_size: GRID_SIZE) \
        -> MultiPoint | MultiLineString | MultiPolygon | None:
    """
    Build MultiPoint, MultiLineString, or MultiPolygon from geometries.
    """
    if shape_type in (ShapeType.point, ShapeType.multi_point):
        checker = check_point
        cls = MultiPoint
        dissolver = _dissolve_point
    elif shape_type in (ShapeType.linestring, ShapeType.multi_linestring):
        checker = check_linestring
        cls = MultiLineString
        dissolver = _dissolve_linestring
    elif shape_type in (ShapeType.polygon, ShapeType.multi_polygon):
        checker = check_polygon
        cls = MultiPolygon
        dissolver = _dissolve_polygon
    else:  # pragma: no cover
        raise ValueError(f'Unsupported shape type: {shape_type}')
    geoms = []
    _check_geometries(geometries, checker=checker, geoms=geoms)
    if len(geoms) <= 1:
        return cls(geoms)
    return dissolver(geoms, grid_size=grid_size)
# End build_dissolved function


def _multi_polygon(features: FeatureClass | ndarray, select_sql: str | None,
                   transformer: Callable | None) -> MultiPolygon:
    """
    Build MultiPolygon from Polygon or MultiPolygon Feature Class or Geometries
    """
    checker = check_polygon
    if isinstance(features, FeatureClass):
        geoms = _get_validated_geoms(
            features, select_sql=select_sql, checker=checker,
            transformer=transformer)
    else:
        geoms = []
        _check_geometries(features, checker=checker, geoms=geoms)
        geoms = asarray(geoms, dtype=object)
    if not len(geoms):
        return MultiPolygon()
    multi = union_all(normalize(geoms)).normalize()
    if not hasattr(multi, GEOMS_ATTR):
        # noinspection PyTypeChecker
        multi = MultiPolygon([multi])
    prepare(multi)
    return multi
# End _multi_polygon function


def _multi_linestring(features: FeatureClass | ndarray, select_sql: str | None,
                      transformer: Callable | None) -> MultiLineString:
    """
    Build MultiLineString from LineString or MultiLineString Feature Class
    or Geometries
    """
    geoms = []
    checker = check_linestring
    if isinstance(features, FeatureClass):
        geoms = _get_validated_geoms(
            features, select_sql=select_sql, checker=checker,
            transformer=transformer)
        geoms = geoms.tolist()
    else:
        _check_geometries(features, checker=checker, geoms=geoms)
    multi = MultiLineString(geoms)
    prepare(multi)
    return multi
# End _multi_linestring function


def _multi_point(features: FeatureClass | ndarray, select_sql: str | None,
                 transformer: Callable | None) -> MultiPoint:
    """
    Build MultiPoint from Point or MultiPoint Feature Class
    """
    checker = check_point
    if isinstance(features, FeatureClass):
        geoms = _get_validated_geoms(
            features, select_sql=select_sql, checker=checker,
            transformer=transformer)
    else:
        geoms = []
        _check_geometries(features, checker=checker, geoms=geoms)
        geoms = asarray(geoms, dtype=object)
    multi = MultiPoint(geoms)
    prepare(multi)
    return multi
# End _multi_point function


def _dissolve_point(geoms: ndarray | list, grid_size: GRID_SIZE) -> MultiPoint:
    """
    Dissolve Points
    """
    points = union_all(geoms, grid_size=grid_size)
    # noinspection PyTypeChecker
    return MultiPoint(get_geoms_iter(points))
# End _dissolve_point function


def _dissolve_linestring(geoms: ndarray | list,
                         grid_size: GRID_SIZE) -> MultiLineString:
    """
    Dissolve LineStrings (combining done during extend_records via the
    geometry configuration combiner)
    """
    lines = union_all(geoms, grid_size=grid_size)
    # noinspection PyTypeChecker
    return MultiLineString(get_geoms_iter(lines))
# End _dissolve_linestring function


def _dissolve_polygon(geoms: ndarray | list,
                      grid_size: GRID_SIZE) -> MultiPolygon:
    """
    Dissolve Polygons
    """
    polys = union_all(normalize(geoms), grid_size=grid_size).normalize()
    # noinspection PyTypeChecker
    return MultiPolygon(get_geoms_iter(polys))
# End _dissolve_polygon function


if __name__ == '__main__':  # pragma: no cover
    pass
