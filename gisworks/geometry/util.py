# -*- coding: utf-8 -*-
"""
Utility Functions
"""


from functools import cached_property
from typing import Any, TYPE_CHECKING, Union
from warnings import warn

from numpy import isnan, ndarray
from shapely import (
    MultiLineString, MultiPolygon, Polygon, set_precision as _set_precision,
    coverage_simplify, force_2d, force_3d)
from shapely.constructive import make_valid, polygonize
from shapely.coordinates import get_coordinates
from shapely.io import from_wkb, from_wkt
from shapely.linear import line_merge

from gisworks.geometry.enumeration import DimensionOption
from gisworks.shared.constant import GEOMS_ATTR
from gisworks.shared.exception import OperationsWarning

if TYPE_CHECKING:  # pragma: no cover
    from shapely.geometry.base import (
        BaseMultipartGeometry, BaseGeometry, GeometrySequence)


def nada(value: Any) -> Any:
    """
    Nada
    """
    return value
# End nada function


def get_geoms(geom: 'BaseMultipartGeometry') -> 'GeometrySequence':
    """
    Get Geometries
    """
    return getattr(geom, GEOMS_ATTR)
# End get_geoms function


def get_geoms_iter(geom: Union['BaseGeometry', 'BaseMultipartGeometry']) \
        -> Union['GeometrySequence', list['BaseGeometry']]:
    """
    Get Geometries for Iteration
    """
    return getattr(geom, GEOMS_ATTR, [geom])
# End get_geoms_iter function


def filter_features(features: list[tuple]) -> list[tuple]:
    """
    Filter Features, removing empty
    """
    return [feature for feature in features if not feature[0].is_empty]
# End filter_features function


def to_shapely(features: list[tuple], option: DimensionOption = DimensionOption.SAME) -> Union[list, 'ndarray']:
    """
    To Shapely Geometry from Fudgeo
    """
    geometries = [from_wkb(g.wkb) for g, *_ in features]
    if option == DimensionOption.TWO_D:
        # noinspection PyTypeChecker
        return force_2d(geometries)
    elif option == DimensionOption.THREE_D:
        # noinspection PyTypeChecker
        return force_3d(geometries)
    return geometries
# End to_shapely function


def set_precision(geometry, grid_size, mode='valid_output', **kwargs):
    """
    Set Precision
    """
    if USE_WORKAROUNDS.set_precision and grid_size > 0:
        if isinstance(geometry, (list, tuple, ndarray)):
            if not len(geometry):
                is_polygon = has_m = False
            else:
                sniff = min(25, len(geometry))
                is_polygon = any(isinstance(g, (Polygon, MultiPolygon))
                                 for g in geometry[:sniff])
                has_m = any(g.has_m for g in geometry[:sniff])
        else:
            is_polygon = isinstance(geometry, (Polygon, MultiPolygon))
            has_m = geometry.has_m
        if is_polygon and has_m:
            warn(f'Setting precision on measured polygons changes the measure '
                 f'value for the last point in the polygon. '
                 f'ref shapely/shapely#2402', OperationsWarning)
    return _set_precision(geometry, grid_size=grid_size, mode=mode, **kwargs)
# End set_precision function


class _UseWorkarounds:
    """
    Use Workarounds for Shapely / GEOS
    """
    @cached_property
    def make_valid(self) -> bool:
        """
        Use workaround for make_valid?
        """
        a = from_wkt('Polygon ((0 0 0 0, 1 1 1 1, 0 1 2 3, 1 0 4 5, 0 0 0 0))')
        result = make_valid(a)
        return not result.has_m
    # End make_valid property

    @cached_property
    def line_merge(self) -> bool:
        """
        Use workaround for line_merge?
        """
        a = from_wkt('LINESTRING (0 0 0 0, 1 1 1 1)')
        b = from_wkt('LINESTRING (1 1 1 1, 2 2 2 2)')
        # noinspection PyTypeChecker
        result = line_merge(MultiLineString([a, b]))
        # noinspection PyUnresolvedReferences
        return not result.has_m
    # End line_merge property

    @cached_property
    def simplify(self) -> bool:
        """
        Use workaround for simplify?
        """
        a = from_wkt('LINESTRING (0 0 0 0, 0 2 2 2, 0 1 1 1)')
        result = a.simplify(0)
        return not result.has_m
    # End simplify property

    @cached_property
    def coverage_simplify(self) -> bool:
        """
        Use workaround for coverage_simplify?
        """
        a = from_wkt('Polygon ((0 0 0 0, 0 1 1 1, 1 1 2 3, 1 0 4 5, 0 0 6 7))')
        # noinspection PyTypeChecker
        result = coverage_simplify(a, tolerance=0.001)
        return not result.has_m
    # End coverage_simplify property

    @cached_property
    def set_precision(self) -> bool:
        """
        Use workaround for set_precision?
        """
        a = from_wkt('Polygon ((0 0 0 0, 0 1 1 1, 1 1 2 3, 1 0 4 5, 0 0 6 7))')
        result = _set_precision(a, grid_size=0.001)
        coords = get_coordinates(result, include_m=True)
        return bool(isnan(coords[:, 2]).any())
    # End set_precision property

    @cached_property
    def polygonize(self) -> bool:
        """
        Use workaround for polygonize?
        """
        a = from_wkt('LINESTRING (0 0 0 0, 0 1 1 1, 1 1 2 3, 1 0 4 5, 0 0 6 7)')
        result = polygonize([a])
        return not result.has_m
    # End polygonize property

    @cached_property
    def point_intersection(self) -> bool:
        """
        Use workaround for Point / Point Z not getting M during intersect?
        """
        a = from_wkt('LineString (0 0 100 200, 10 0 300 400)')
        p = from_wkt('Point (2 0)')
        return not p.intersection(a).has_m
    # End point_intersection property

    @cached_property
    def point_interpolation(self) -> bool:
        """
        Use workaround for Point getting bad Z value during intersect?
        """
        a = from_wkt('LineString (0 0 100 200, 10 0 300 400)')
        b = from_wkt('Point (2 0)')
        # noinspection PyUnresolvedReferences
        return a.intersection(b).z != 140
    # End point_interpolation property

    @cached_property
    def geometry_order_interpolation(self) -> bool:
        """
        Use workaround for Geometry Order affecting ZM interpolation?
        """
        a = from_wkt('LineString (0 0 100 200, 10 0 300 400)')
        b = from_wkt('LineString (2 0, 5 0, 8 0)')
        result = b.intersection(a)
        coords = get_coordinates(result, include_m=True)
        return bool(isnan(coords[:, 2]).any())
    # End geometry_order_interpolation property

    @cached_property
    def inconsistent_zm_source(self) -> bool:
        """
        Use workaround for ZM values sourced from both inputs?
        """
        from shapely import from_wkt
        a = from_wkt('LineString (2 0 1111 2222, 5 0 3333 4444, 8 0 5555 6666)')
        b = from_wkt('LineString (0 0 1 2, 3 0 3 4, 6 0 5 6, 8 0 7 8)')
        bad = from_wkt('LineString (2 0 1111 2222, 3 0 3 4)')
        result = a.intersection(b)
        return bad in set(get_geoms(result))
    # End inconsistent_zm_source property

    @cached_property
    def dropped_nan_measures(self) -> bool:
        """
        Use workaround for NaN measures completely dropped when intersecting
        LineString and MultiLineString with ZM values
        """
        line_a = from_wkt('LineString (0 0 0 NaN, 10 0 123 NaN)')
        line_b = from_wkt('LineString (4 -5 999 NaN, 5 5 456 NaN, 6 -6 678 NaN)')
        # noinspection PyTypeChecker
        line_b = MultiLineString([line_b])
        result = line_a.intersection(line_b)
        return not result.has_m
    # End dropped_nan_measures property
# End _UseWorkarounds class


USE_WORKAROUNDS: _UseWorkarounds = _UseWorkarounds()


if __name__ == '__main__':  # pragma: no cover
    pass
