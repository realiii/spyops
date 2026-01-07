# -*- coding: utf-8 -*-
"""
Types
"""


from typing import NamedTuple, TYPE_CHECKING, Union

from fudgeo import FeatureClass
from shapely import Polygon

from gisworks.geometry.config import GeometryConfig

if TYPE_CHECKING:  # pragma: no cover
    from gisworks.query.base import AbstractQuery, AbstractSpatialQuery


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
    planarized: list[Polygon]
    polygons: list[Polygon]
    ids: list[int]
# End PlanarizeResults class


class QueryConfig(NamedTuple):
    """
    Query Config
    """
    source: FeatureClass
    target: FeatureClass
    disjoint: str
    insert: str
    config: GeometryConfig
# End QueryConfig class


if __name__ == '__main__':  # pragma: no cover
    pass
