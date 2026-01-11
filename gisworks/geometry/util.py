# -*- coding: utf-8 -*-
"""
Utility Functions
"""


from functools import cached_property
from typing import Any, TYPE_CHECKING, Union

from fudgeo.constant import FETCH_SIZE
from numpy import isnan
from shapely import MultiLineString, set_precision, coverage_simplify
from shapely.constructive import make_valid, polygonize
from shapely.coordinates import get_coordinates
from shapely.io import from_wkb, from_wkt
from shapely.linear import line_merge

from gisworks.shared.constant import GEOMS_ATTR
from gisworks.shared.util import extend_records


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo.context import ExecuteMany
    from shapely.geometry.base import (
        BaseMultipartGeometry, BaseGeometry, GeometrySequence)
    from sqlite3 import Cursor
    from gisworks.geometry.config import GeometryConfig


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
    return getattr(geom, GEOMS_ATTR, [geom,])
# End get_geoms_iter function


def filter_features(features: list[tuple]) -> list[tuple]:
    """
    Filter Features, removing empty
    """
    return [feature for feature in features if not feature[0].is_empty]
# End filter_features function


def to_shapely(features: list[tuple]) -> list:
    """
    To Shapely Geometry from Fudgeo
    """
    return [from_wkb(g.wkb) for g, *_ in features]
# End to_shapely function


def bulk_insert(cursor: 'Cursor', config: 'GeometryConfig',
                executor: 'ExecuteMany', insert_sql: str) -> None:
    """
    Bulk Insert
    """
    records = []
    while features := cursor.fetchmany(FETCH_SIZE):
        if not (features := filter_features(features)):
            continue
        geometries = to_shapely(features)
        results = [(g, attrs) for g, (_, *attrs) in zip(geometries, features)]
        extend_records(results, records=records, config=config)
        executor(sql=insert_sql, data=records)
        records.clear()
# End bulk_insert function


class UseWorkarounds:
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
        result = coverage_simplify(a, tolerance=0.001)
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
    def polygonize(self) -> bool:
        """
        Use workaround for polygonize?
        """
        a = from_wkt('LINESTRING (0 0 0 0, 0 1 1 1, 1 1 2 3, 1 0 4 5, 0 0 6 7)')
        result = polygonize([a])
        return not result.has_m
    # End polygonize property
# End UseWorkarounds class


USE_WORKAROUNDS: UseWorkarounds = UseWorkarounds()


if __name__ == '__main__':  # pragma: no cover
    pass
