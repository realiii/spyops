# -*- coding: utf-8 -*-
"""
Types
"""


from typing import Any, NamedTuple

from shapely import (
    MultiPolygon as ShapelyMultiPolygon, Polygon as ShapelyPolygon)


class QueryComponents(NamedTuple):
    """
    Spatial Query Components
    """
    use_index: bool
    has_intersection: bool
    sql_touches: str
    sql_outside: str
    sql_insert: str
# End QueryComponents class


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
