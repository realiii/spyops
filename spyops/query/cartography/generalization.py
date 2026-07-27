# -*- coding: utf-8 -*-
"""
Query Classes for cartography.generalization module
"""


from typing import Callable, TYPE_CHECKING

from spyops.geometry.smooth import smooth_bezier, smooth_paek
from spyops.geometry.wa import simplify
from spyops.query.base import AbstractSourceQuery
from spyops.shared.enumeration import (
    SimplifyAlgorithmOption, SmoothAlgorithmOption)
from spyops.shared.hint import XY_TOL


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass


class BaseQuerySimplify(AbstractSourceQuery):
    """
    Base Query Simplify
    """
    def __init__(self, source: 'FeatureClass', target: 'FeatureClass', *,
                 algorithm_option: SimplifyAlgorithmOption,
                 where_clause: str, xy_tolerance: XY_TOL) -> None:
        """
        Initialize the BaseQuerySimplify class
        """
        super().__init__(source, target=target, where_clause=where_clause,
                         xy_tolerance=xy_tolerance)
        self._option: SimplifyAlgorithmOption = algorithm_option
    # End init built-in

    @property
    def simplifier(self) -> Callable:
        """
        Simplifier
        """
        return simplify
    # End simplifier property

    @property
    def insert(self) -> str:
        """
        Insert Query
        """
        elm = self.target
        field_count, insert_field_names, _ = self._field_names_and_count(elm)
        return self._make_insert(
            elm.escaped_name, field_names=insert_field_names,
            field_count=field_count)
    # End insert property
# End BaseQuerySimplify class


class QuerySimplifyLine(BaseQuerySimplify):
    """
    Query Simplify Line
    """
# End QuerySimplifyLine class


class QuerySimplifyPolygon(BaseQuerySimplify):
    """
    Query Simplify Polygon
    """
# End QuerySimplifyPolygon class


class BaseQuerySmooth(AbstractSourceQuery):
    """
    Base Query Smooth
    """
    def __init__(self, source: 'FeatureClass', target: 'FeatureClass', *,
                 algorithm_option: SmoothAlgorithmOption,
                 where_clause: str, xy_tolerance: XY_TOL) -> None:
        """
        Initialize the BaseQuerySmooth class
        """
        super().__init__(source, target=target, where_clause=where_clause,
                         xy_tolerance=xy_tolerance)
        self._option: SmoothAlgorithmOption = algorithm_option
    # End init built-in

    @property
    def smoother(self) -> Callable:
        """
        Smoother
        """
        if self._option == SmoothAlgorithmOption.BEZIER:
            return smooth_bezier
        else:
            return smooth_paek
    # End smoother property

    @property
    def insert(self) -> str:
        """
        Insert Query
        """
        elm = self.target
        field_count, insert_field_names, _ = self._field_names_and_count(elm)
        return self._make_insert(
            elm.escaped_name, field_names=insert_field_names,
            field_count=field_count)
    # End insert property
# End BaseQuerySmooth class


class QuerySmoothLine(BaseQuerySmooth):
    """
    Query Smooth Line
    """
# End QuerySmoothLine class


if __name__ == '__main__':  # pragma: no cover
    pass
