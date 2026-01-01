# -*- coding: utf-8 -*-
"""
Types
"""


from typing import Any, Callable, NamedTuple, TYPE_CHECKING, Union

from fudgeo import FeatureClass
from shapely import (
    MultiPolygon as ShapelyMultiPolygon, Polygon as ShapelyPolygon)


if TYPE_CHECKING:  # pragma: no cover
    from geomio.query.base import AbstractQuery, AbstractSpatialQuery


class AnalysisComponents(NamedTuple):
    """
    Spatial Analysis Components
    """
    has_intersection: bool
    query: Union['AbstractQuery', 'AbstractSpatialQuery']
    target: FeatureClass
# End AnalysisComponents class


class PlanarizeResults(NamedTuple):
    """
    Planarize Results
    """
    planarized: list[ShapelyPolygon]
    polygons: list[ShapelyPolygon]
    ids: list[int]
# End PlanarizeResults class


class GeometryConfig(NamedTuple):
    """
    Geometry Configuration
    """
    fudgeo_cls: Any
    is_multi: bool
    shapely_multi_cls: Any
    shapely_types: tuple
    srs_id: int
    combiner: Callable
# End GeometryConfig class


if __name__ == '__main__':  # pragma: no cover
    pass
