# -*- coding: utf-8 -*-
"""
Query Classes for management.generalization module
"""


from functools import partial
from typing import Callable

from fudgeo.enumeration import ShapeType

from spyops.geometry.multi import build_dissolved
from spyops.query.management.shared import AbstractQueryDissolveStatistics


class QueryDissolve(AbstractQueryDissolveStatistics):
    """
    Queries for Dissolve
    """
    def _get_target_shape_type(self) -> str:
        """
        Get Target Shape Type based on Output Type Option and Source Shape Type
        """
        if (self._as_multi_part and self.source.is_multi_part) or (
                not self._as_multi_part and not self.source.is_multi_part):
            return self.source.shape_type
        lut = {ShapeType.polygon: ShapeType.multi_polygon,
               ShapeType.linestring: ShapeType.multi_linestring,
               ShapeType.point: ShapeType.multi_point,
               ShapeType.multi_point: ShapeType.point,
               ShapeType.multi_linestring: ShapeType.linestring,
               ShapeType.multi_polygon: ShapeType.polygon}
        return lut[self.source.shape_type]
    # End _get_target_shape_type method

    def _get_builder(self, shape_type: str) -> Callable:
        """
        Get Builder based on Shape Type
        """
        return partial(
            build_dissolved, shape_type=shape_type, grid_size=self.grid_size)
    # End _get_builder method
# End QueryDissolve class


if __name__ == '__main__':  # pragma: no cover
    pass
