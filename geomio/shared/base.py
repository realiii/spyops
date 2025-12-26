# -*- coding: utf-8 -*-
"""
Types
"""


from typing import Any, NamedTuple, TYPE_CHECKING, Union

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


class OverlayConfig(NamedTuple):
    """
    Overlay Configuration
    """
    fudgeo_cls: Any
    is_multi: bool
    shapely_multi_cls: Any
    shapely_types: tuple
    geometry: ShapelyMultiPolygon | ShapelyPolygon
    srs_id: int
# End OverlayConfig class


if __name__ == '__main__':  # pragma: no cover
    pass
