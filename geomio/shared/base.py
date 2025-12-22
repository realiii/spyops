# -*- coding: utf-8 -*-
"""
Types
"""


from typing import Any, NamedTuple

from fudgeo import FeatureClass
from shapely import (
    MultiPolygon as ShapelyMultiPolygon, Polygon as ShapelyPolygon)


class AnalysisComponents(NamedTuple):
    """
    Spatial Analysis Components
    """
    use_index: bool
    has_intersection: bool
    sql_intersect: str
    sql_disjoint: str
    sql_insert: str
    target: FeatureClass
# End AnalysisComponents class


class OverlayConfig(NamedTuple):
    """
    Overlay Configuration
    """
    fudgeo_cls: Any
    is_multi: bool
    shapely_multi_cls: Any
    shapely_types: tuple
    geometry: ShapelyMultiPolygon | ShapelyPolygon
# End OverlayConfig class


if __name__ == '__main__':  # pragma: no cover
    pass
