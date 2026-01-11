# -*- coding: utf-8 -*-
"""
Validate Geometry
"""


from operator import eq, ge
from typing import TYPE_CHECKING, Type, Optional, Union

from fudgeo.enumeration import GeometryType

from shapely import (
    LineString, MultiLineString, MultiPoint, MultiPolygon, Point, Polygon)
from shapely.constructive import make_valid

from gisworks.shared.constant import GEOMS_ATTR
from gisworks.shared.exception import OperationsError


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass
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
    geoms = [p for p in getattr(geom, GEOMS_ATTR, [geom])
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
    if shape_type in (GeometryType.point, GeometryType.multi_point):
        return 0
    elif shape_type in (GeometryType.linestring, GeometryType.multi_linestring):
        return 1
    elif shape_type in (GeometryType.polygon, GeometryType.multi_polygon):
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
    dim_type = {0: GeometryType.point,
                1: GeometryType.linestring,
                2: GeometryType.polygon}
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


if __name__ == '__main__':  # pragma: no cover
    pass
