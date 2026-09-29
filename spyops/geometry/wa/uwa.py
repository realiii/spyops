# -*- coding: utf-8 -*-
"""
Checks on Workarounds for Shapely / GEOS
"""

from functools import cached_property
from typing import TYPE_CHECKING

from numpy import isnan
from pyproj import CRS
from shapely import MultiLineString, coverage_simplify, set_precision
from shapely.constructive import make_valid, polygonize, segmentize, simplify
from shapely.coordinates import get_coordinates
from shapely.io import from_wkt
from shapely.linear import line_interpolate_point, line_merge
from shapely.ops import transform

from spyops.crs.constant import WGS84
from spyops.crs.transform import get_transforms
from spyops.geometry.util import get_geoms


if TYPE_CHECKING:  # pragma: no cover
    from shapely.geometry.base import BaseGeometry


class _UseWorkarounds:
    """
    Use Workarounds for Shapely / GEOS
    """
    @cached_property
    def transform(self) -> bool:
        """
        Use workaround for transform (does not support Z and M because
        set_coordinates does not support Z and M)
        """
        a = from_wkt('Point (0 0 0 0)')
        _, best, _ = get_transforms(source_crs=WGS84, target_crs=CRS(3857))
        try:
            transform(best.transform, a)
            return False
        except ValueError:
            return True
    # End transform property

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
        return not result.has_m
    # End line_merge property

    @cached_property
    def line_interpolate_point(self) -> bool:
        """
        Use workaround for line_interpolate_point?
        """
        a = from_wkt('LINESTRING (0 0 0 0, 10 20 30 40, 100 200 300 400)')
        # noinspection PyTypeChecker
        result = line_interpolate_point(a, distance=0.5, normalized=True)
        return not result.has_m
    # End line_interpolate_point property

    @cached_property
    def simplify(self) -> bool:
        """
        Use workaround for simplify?
        """
        a = from_wkt('LINESTRING (0 0 0 0, 0 2 2 2, 0 1 1 1)')
        result = simplify(a, tolerance=0)
        return not result.has_m
    # End simplify property

    @cached_property
    def coverage_simplify(self) -> bool:
        """
        Use workaround for coverage_simplify?
        """
        a = from_wkt('Polygon ((0 0 0 0, 0 1 1 1, 1 1 2 3, 1 0 4 5, 0 0 6 7))')
        # noinspection PyTypeChecker
        result: BaseGeometry = coverage_simplify(a, tolerance=0.001)
        return not result.has_m
    # End coverage_simplify property

    @cached_property
    def set_precision(self) -> bool:
        """
        Use workaround for set_precision?
        """
        a = from_wkt('Polygon ((0 0 0 0, 0 1 1 1, 1 1 2 3, 1 0 4 5, 0 0 6 7))')
        result = set_precision(a, grid_size=0.001)
        coords = get_coordinates(result, include_m=True)
        return bool(isnan(coords[:, 2]).any())
    # End set_precision property

    @cached_property
    def polygonize_drop_m(self) -> bool:
        """
        Use workaround for polygonize when it drops M values?
        """
        a = from_wkt('LINESTRING (0 0 0 0, 0 1 1 1, 1 1 2 3, 1 0 4 5, 0 0 6 7)')
        result = polygonize([a])
        return not result.has_m
    # End polygonize_drop_m property

    @cached_property
    def polygonize_drop_z_nan(self) -> bool:
        """
        Use workaround for polygonize when it drops Z values if all nan?
        """
        a = from_wkt('LINESTRING (0 0 NaN, 0 1 NaN, 1 1 NaN, 1 0 NaN, 0 0 NaN)')
        result = polygonize([a])
        return not result.has_z
    # End polygonize_drop_z_nan property

    @property
    def polygonize(self) -> bool:
        """
        Use workaround for any polygonize issue?
        """
        return any((self.polygonize_drop_m, self.polygonize_drop_z_nan))
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
        a = from_wkt('LineString (2 0 1111 2222, 5 0 3333 4444, 8 0 5555 6666)')
        b = from_wkt('LineString (0 0 1 2, 3 0 3 4, 6 0 5 6, 8 0 7 8)')
        bad = from_wkt('LineString (2 0 1111 2222, 3 0 3 4)')
        result = a.intersection(b)
        # noinspection PyTypeChecker
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

    @cached_property
    def segmentize(self) -> bool:
        """
        Use workout for segmentize when operating on measured feature
        """
        line = from_wkt('LineString (0 0 0 100, 10 0 123 200)')
        densified = segmentize(line, max_segment_length=2)
        return not densified.has_m
    # End segmentize property
# End _UseWorkarounds class


USE_WORKAROUNDS: _UseWorkarounds = _UseWorkarounds()


if __name__ == '__main__':  # pragma: no cover
    pass
