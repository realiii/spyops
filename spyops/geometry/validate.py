# -*- coding: utf-8 -*-
"""
Validate Geometry
"""


from operator import eq, ge
from typing import Callable, TYPE_CHECKING, Type, Optional, Union

from fudgeo.constant import FETCH_SIZE
from fudgeo.enumeration import ShapeType
from numpy import asarray

from shapely import (
    LineString, MultiLineString, MultiPoint, MultiPolygon, Point, Polygon)

from spyops.geometry.enumeration import DimensionOption
from spyops.geometry.util import get_geoms_iter, nada, to_shapely
from spyops.geometry.wa import make_valid
from spyops.shared.exception import OperationsError


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass
    from numpy import ndarray
    from shapely.geometry.base import BaseGeometry, BaseMultipartGeometry


def check_polygon(polygon: Polygon | MultiPolygon) \
        -> MultiPolygon | Polygon | None:
    """
    Check Polygon
    """
    return _check_geometry(
        polygon, method_name='structure', cls=Polygon,
        multi_cls=MultiPolygon)
# End check_polygon function


def check_linestring(geom: LineString | MultiLineString) \
        -> LineString | MultiLineString | None:
    """
    Check LineString
    """
    return _check_geometry(
        geom, method_name='linework', cls=LineString,
        multi_cls=MultiLineString)
# End check_linestring function


def check_point(geom: Point | MultiPoint) -> Point | MultiPoint | None:
    """
    Check Point
    """
    if geom.is_empty:
        return None
    return geom
# End check_point function


def _check_geometry(geom: 'BaseGeometry', method_name: str,
                    cls: Type['BaseGeometry'],
                    multi_cls: Type['BaseMultipartGeometry']) \
        -> Optional[Union['BaseGeometry', 'BaseMultipartGeometry']]:
    """
    Check Geometry (for LineString and Polygon)
    """
    if geom.is_valid:
        return geom
    # noinspection PyTypeChecker
    geom = make_valid(geom, method=method_name)
    if not geom.is_valid:
        return None
    geoms = [p for p in get_geoms_iter(geom)
             if p.is_valid and isinstance(p, cls)]
    if not geoms:
        return None
    if len(geoms) == 1:
        return geoms[0]
    # noinspection PyArgumentList
    return multi_cls(geoms)
# End _check_geometry function


def get_geometry_dimension(feature_class: 'FeatureClass') -> int:
    """
    Get Geometry Dimension
    """
    shape_type = feature_class.shape_type
    if shape_type in (ShapeType.point, ShapeType.multi_point):
        return 0
    elif shape_type in (ShapeType.linestring, ShapeType.multi_linestring):
        return 1
    elif shape_type in (ShapeType.polygon, ShapeType.multi_polygon):
        return 2
    return -1
# End get_geometry_dimension function


def get_geometry_zm(feature_class: 'FeatureClass') -> tuple[bool, bool]:
    """
    Get Geometry Dimension
    """
    return feature_class.has_z, feature_class.has_m
# End get_geometry_zm function


def check_dimension(a: int, name_a: str, b: int, name_b: str,
                    same: bool = False) -> None:
    """
    Check integers representing geometry dimension

    The default implementation is that b must be same or higher dimension
    than a, or in more concrete terms, the operator must have same or higher
    dimension than the source.

    When same=True, the operator must have same dimension as source.
    """
    if same:
        op = eq
    else:
        op = ge
    if op(b, a):
        return
    dim_type = {0: ShapeType.point,
                1: ShapeType.linestring,
                2: ShapeType.polygon}
    raise OperationsError(
        f'Geometry dimension mismatch, cannot overlay '
        f'{name_a} {dim_type[a]} with {name_b} {dim_type[b]}')
# End check_dimension function


def check_zm(a: tuple[bool, bool], name_a: str,
             b: tuple[bool, bool], name_b: str) -> None:
    """
    Check extended geometry properties ZM, ensure match.
    """
    if a == b:
        return
    stub = 'has_z=%s / has_m=%s'
    props_a = stub % a
    props_b = stub % b
    raise OperationsError(
        f'Geometry ZM mismatch, cannot overlay '
        f'{name_a} {props_a} with {name_b} {props_b}')
# End check_zm function


def get_validated_geometries(feature_class: 'FeatureClass',
                             transformer: Callable | None) -> 'ndarray':
    """
    Get Validated Geometries forced to 2D
    """
    shape_type = feature_class.shape_type
    if shape_type in (ShapeType.point, ShapeType.multi_point):
        checker = check_point
    elif shape_type in (ShapeType.linestring, ShapeType.multi_linestring):
        checker = check_linestring
    elif shape_type in (ShapeType.polygon, ShapeType.multi_polygon):
        checker = check_polygon
    else:
        checker = nada
    return _get_validated_geoms(
        feature_class, checker=checker, transformer=transformer)
# End get_validated_geometries function


def _get_validated_geoms(feature_class: 'FeatureClass', checker: Callable,
                         transformer: Callable | None) -> 'ndarray':
    """
    Get Shapely Geometries from Feature Class, forcing to 2D.
    """
    geoms = []
    cursor = feature_class.select()
    while features := cursor.fetchmany(FETCH_SIZE):
        geometries, validity = to_shapely(
            features, transformer=transformer, option=DimensionOption.TWO_D)
        _check_geometries(geometries[validity], checker=checker, geoms=geoms)
    return asarray(geoms, dtype=object)
# End _get_validated_geoms function


def _check_geometries(geometries: 'ndarray', checker: Callable,
                      geoms: list) -> None:
    """
    Check Geometries for validity and fix issues where possible
    """
    for geometry in geometries:
        for geom in get_geoms_iter(geometry):
            if checker(geom) is None:
                continue
            geoms.append(geom)
# End _check_geometries function


if __name__ == '__main__':  # pragma: no cover
    pass
