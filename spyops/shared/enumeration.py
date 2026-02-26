# -*- coding: utf-8 -*-
"""
Enumerations
"""


from enum import IntFlag, STRICT, StrEnum, auto


class AttributeOption(StrEnum):
    """
    Attribute Options
    """
    ALL = auto()
    SANS_FID = auto()
    ONLY_FID = auto()
# End AttributeOption class


class AlgorithmOption(StrEnum):
    """
    Algorithm Options
    """
    CLASSIC = auto()
    PAIRWISE = auto()
# End AlgorithmOption class


class OutputTypeOption(StrEnum):
    """
    Output Type Options
    """
    SAME = auto()
    LINE = auto()
    POINT = auto()
# End OutputTypeOption class


class FieldProperty(StrEnum):
    """
    Field Properties
    """
    ALIAS = auto()
    COMMENT = auto()
    NAME = auto()
# End FieldProperty class


class WeightOption(StrEnum):
    """
    Weight Options
    """
    TWO_D = auto()
    THREE_D = auto()
# End WeightOption class


class GeometryAttribute(StrEnum):
    """
    GeometryAttributes
    """
    POINT_X = auto()
    POINT_Y = auto()
    POINT_Z = auto()
    POINT_M = auto()

    CENTROID_X = auto()
    CENTROID_Y = auto()
    CENTROID_Z = auto()
    CENTROID_M = auto()

    PART_COUNT = auto()
    POINT_COUNT = auto()
    HOLE_COUNT = auto()

    EXTENT_MIN_X = auto()
    EXTENT_MIN_Y = auto()
    EXTENT_MIN_Z = auto()
    EXTENT_MIN_M = auto()

    EXTENT_MAX_X = auto()
    EXTENT_MAX_Y = auto()
    EXTENT_MAX_Z = auto()
    EXTENT_MAX_M = auto()

    LENGTH = auto()
    LENGTH_GEODESIC = auto()

    LINE_AZIMUTH = auto()

    LINE_START_X = auto()
    LINE_START_Y = auto()
    LINE_START_Z = auto()
    LINE_START_M = auto()

    LINE_END_X = auto()
    LINE_END_Y = auto()
    LINE_END_Z = auto()
    LINE_END_M = auto()

    INSIDE_X = auto()
    INSIDE_Y = auto()

    AREA = auto()
    AREA_GEODESIC = auto()

    PERIMETER = auto()
    PERIMETER_GEODESIC = auto()
# End GeometryAttribute class


class GeometryCheck(IntFlag, boundary=STRICT):
    """
    Geometry Check Options
    """
    EXTENT = auto()

    EMPTY = auto()
    EMPTY_PART = auto()
    EMPTY_POINT = auto()
    POINT_COUNT = auto()

    EMPTY_RING = auto()
    ORIENTATION = auto()
    UNCLOSED = auto()
    SELF_INTERSECTION = auto()
    OUTSIDE_RING = auto()
    OVERLAP_RING = auto()

    NAN_Z = auto()
    NAN_M = auto()
    REPEATED_XY = auto()
    REPEATED_M = auto()
    MISMATCH_Z = auto()
    MISMATCH_M = auto()
# End GeometryCheck class


DEFAULT_GEOM_CHECKS: GeometryCheck = (
    GeometryCheck.EXTENT | GeometryCheck.EMPTY | GeometryCheck.EMPTY_PART |
    GeometryCheck.EMPTY_RING | GeometryCheck.EMPTY_POINT |
    GeometryCheck.NAN_Z | GeometryCheck.NAN_M |
    GeometryCheck.REPEATED_XY | GeometryCheck.REPEATED_M |
    GeometryCheck.MISMATCH_Z | GeometryCheck.MISMATCH_M
)


if __name__ == '__main__':  # pragma: no cover
    pass
