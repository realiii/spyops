# -*- coding: utf-8 -*-
"""
Queries for Features
"""

from abc import ABCMeta
from functools import partial
from typing import Callable, TYPE_CHECKING

from fudgeo import Field
from fudgeo.constant import SHAPE
from fudgeo.enumeration import FieldType
from numpy import array
from shapely import get_coordinates

from spyops.geometry.fill import GEOMETRY_FILL_MISSING_Z
from spyops.geometry.measured import MeasuredLine
from spyops.query.base import AbstractSourceUpdateQuery
from spyops.query.management.sampling import (
    AbstractQueryGeneratePointsAlongLines, AlongLinesDistanceMixin,
    AlongLinesFieldMixin, AlongLinesPercentageMixin)
from spyops.shared.field import ORIG_FID
from spyops.shared.hint import FIELDS, NAMES


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass
    from numpy import ndarray
    from pyproj import CRS
    from shapely import LineString


class AbstractQueryGeneratePointsAlong3DLines(
        AbstractQueryGeneratePointsAlongLines, metaclass=ABCMeta):
    """
    Abstract Query Generate Along Lines 3D
    """
    @property
    def _is_2d(self) -> bool:
        """
        Is 2D
        """
        return False
    # End _is_2d property

    def _get_line_lengths(self, lines: list['LineString'],
                          crs: 'CRS') -> 'ndarray':
        """
        Get Line Lengths
        """
        lengths = []
        factor = self._get_z_factor(crs)
        for line in lines:
            coords = get_coordinates(line, include_z=True)
            measured = MeasuredLine(
                xs=coords[:, 0], ys=coords[:, 1], zs=coords[:, 2] * factor)
            lengths.append(max(measured.measures))
        return array(lengths, dtype=float)
    # End _get_line_lengths method

    def _get_z_factor(self, crs: 'CRS') -> float:
        """
        Get Z Factor
        """
        horizontal = self._get_conversion_factor(crs)
        vertical = self._get_conversion_factor(crs, use_horizontal=False)
        return horizontal / vertical
    # End _get_z_factor method
# End AbstractQueryGenerateAlong3DLines class


class QueryGeneratePointsAlong3DLinesPercentage(
        AlongLinesPercentageMixin, AbstractQueryGeneratePointsAlong3DLines):
    """
    Query for Generate Points Along Lines 3D using Percentage Placement
    """
# End QueryGeneratePointsAlong3DLinesPercentage class


class QueryGeneratePointsAlong3DLinesDistance(
        AlongLinesDistanceMixin, AbstractQueryGeneratePointsAlong3DLines):
    """
    Query for Generate Points Along Lines 3D using Distance Placement
    """
# End QueryGeneratePointsAlong3DLinesDistance class


class QueryGeneratePointsAlong3DLinesField(
        AlongLinesFieldMixin, AbstractQueryGeneratePointsAlong3DLines):
    """
    Query for Generate Points Along Lines 3D using Field Placement
    """
# End QueryGeneratePointsAlong3DLinesField class


class QueryCalculateMissingZValues(AbstractSourceUpdateQuery):
    """
    Queries for Calculate Missing Z Values
    """
    def __init__(self, source: 'FeatureClass',
                 matcher: Callable[['ndarray'], 'ndarray'],
                 where_clause: str) -> None:
        """
        Initialize the QueryCalculateMissingZValues class
        """
        super().__init__(source, where_clause=where_clause)
        self._matcher: Callable[['ndarray'], 'ndarray'] = matcher
    # End init built-in

    def _get_field_names(self) -> NAMES:
        """
        Get Field Names
        """
        return self.source.geometry_column_name,
    # End _get_field_names method

    @property
    def _short_name(self) -> str:
        """
        Short Name
        """
        return 'fill_z'
    # End _short_name property

    def _prepare_source(self) -> None:
        """
        Override
        """
        pass
    # End _prepare_source method

    @property
    def _intermediate_fields(self) -> FIELDS:
        """
        Intermediate Fields
        """
        return ORIG_FID, Field(SHAPE, data_type=FieldType.text)
    # End _intermediate_fields property

    @property
    def z_filler(self) -> Callable:
        """
        Z Filler
        """
        fill_missing_z = GEOMETRY_FILL_MISSING_Z[self.source.shape_type]
        return partial(fill_missing_z, matcher=self._matcher)
    # End z_filler property
# End QueryCalculateMissingZValues class


if __name__ == '__main__':  # pragma: no cover
    pass
