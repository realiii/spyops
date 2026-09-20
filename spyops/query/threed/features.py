# -*- coding: utf-8 -*-
"""
Queries for Features
"""

from abc import ABCMeta

from numpy import array, ndarray
from pyproj import CRS
from shapely import LineString, get_coordinates

from spyops.geometry.measured import MeasuredLine
from spyops.query.management.sampling import (
    AbstractQueryGeneratePointsAlongLines, AlongLinesDistanceMixin,
    AlongLinesFieldMixin, AlongLinesPercentageMixin)


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


if __name__ == '__main__':  # pragma: no cover
    pass
