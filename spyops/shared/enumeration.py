# -*- coding: utf-8 -*-
"""
Enumerations
"""


from enum import IntFlag, STRICT, StrEnum, auto


class LineTypeOption(StrEnum):
    """
    Line Type Options
    """
    GEODESIC = auto()
    PLANAR = auto()
# End LineTypeOption class


class BufferTypeOption(StrEnum):
    """
    Buffer Type Options
    """
    GEODESIC = auto()
    PLANAR = auto()
# End BufferTypeOption class


class SideOption(StrEnum):
    """
    Side Options
    """
    FULL = auto()
    LEFT = auto()
    RIGHT = auto()
    ONLY_OUTSIDE = auto()
# End SideOption class


class EndOption(StrEnum):
    """
    End Options
    """
    ROUND = auto()
    FLAT = auto()
    SQUARE = auto()
# End EndOption class


class DissolveOption(StrEnum):
    """
    Dissolve Options
    """
    ALL = auto()
    LIST = auto()
    NONE = auto()
# End DissolveOption class


class GroupOption(StrEnum):
    """
    Group Options
    """
    ALL = auto()
    LIST = auto()
    NONE = auto()
# End GroupOption class


class MinimumGeometryOption(StrEnum):
    """
    Minimum Geometry Options
    """
    RECTANGLE_BY_AREA = auto()
    RECTANGLE_BY_WIDTH = auto()
    CONVEX_HULL = auto()
    CIRCLE = auto()
    ENVELOPE = auto()
# End MinimumGeometryOption class


class PointTypeOption(StrEnum):
    """
    Point Type Options
    """
    ALL = auto()
    MID = auto()
    START = auto()
    END = auto()
    BOTH_ENDS = auto()
# End PointTypeOption class


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


class SimplifyAlgorithmOption(StrEnum):
    """
    Simplify Algorithm Option
    """
    POINT_REMOVE = auto()
# End SimplifyAlgorithmOption class


class SmoothAlgorithmOption(StrEnum):
    """
    Smooth Algorithm Option
    """
    PAEK = auto()
    BEZIER = auto()
# End SmoothAlgorithmOption class


class OutputTypeOption(StrEnum):
    """
    Output Type Options
    """
    SAME = auto()
    LINE = auto()
    POINT = auto()
# End OutputTypeOption class


class StatisticOutputOption(StrEnum):
    """
    Statistic Output Type Options
    """
    NUMERIC = auto()
    TEXT = auto()
    DATE = auto()
# End StatisticOutputOption class


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
    Geometry Attributes
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


class GeoJSONGeometryType(StrEnum):
    """
    GeoJSON Geometry Type
    """
    AUTO = auto()
    POINT = auto()
    MULTI_POINT = auto()
    LINESTRING = auto()
    MULTI_LINESTRING = auto()
    POLYGON = auto()
    MULTI_POLYGON = auto()
# End GeoJSONGeometryType class


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


class Statistic(StrEnum):
    """
    Statistic
    """
    AVERAGE = auto()
    MEDIAN = auto()
    MINIMUM = auto()
    MAXIMUM = auto()
    RANGE = auto()
    STANDARD_DEVIATION = auto()
    VARIANCE = auto()
    SUMMATION = auto()

    COUNT = auto()
    COUNT_NULL = auto()
    COUNT_NON_NULL = auto()
    UNIQUE = auto()
    MODE = auto()
    FIRST = auto()
    LAST = auto()
    CONCATENATE = auto()

    SKEWNESS = auto()
    KURTOSIS = auto()
    VARIATION = auto()

    FIRST_QUARTILE = auto()
    THIRD_QUARTILE = auto()
    INTERQUARTILE_RANGE = auto()
    COUNT_OUTLIER = auto()

    LEAST_COMMON = auto()
    MOST_COMMON = auto()
# End Statistic class


class SortOrder(StrEnum):
    """
    Sort Order
    """
    ASCENDING = auto()
    DESCENDING = auto()
# End SortOrder class


class AttributeSource(StrEnum):
    """
    Attribute Source
    """
    NONE = auto()
    BOTH = auto()
    START = auto()
    END = auto()
# End AttributeSource class


class SpatialSortOption(StrEnum):
    """
    Spatial Sort Option
    """
    NONE = auto()
    UPPER_LEFT_ASCENDING = auto()
    LOWER_LEFT_ASCENDING = auto()
    UPPER_RIGHT_ASCENDING = auto()
    LOWER_RIGHT_ASCENDING = auto()
    UPPER_LEFT_DESCENDING = auto()
    LOWER_LEFT_DESCENDING = auto()
    UPPER_RIGHT_DESCENDING = auto()
    LOWER_RIGHT_DESCENDING = auto()
# End SpatialSortOption class


class StandardizationMethod(StrEnum):
    """
    Standardization Method
    """
    Z_SCORE = auto()
    MIN_MAX = auto()
    ABSOLUTE_MAX = auto()
    ROBUST = auto()
# End StandardizationMethod class


class TransformationMethod(StrEnum):
    """
    Transformation Method
    """
    INVERSE = auto()
    SQUARE_ROOT = auto()
    SQUARE = auto()
    LOGARITHM = auto()
    EXPONENTIAL = auto()
    BOX_COX = auto()
    INVERSE_BOX_COX = auto()
# End TransformationMethod class


class ReclassificationMethod(StrEnum):
    """
    Reclassification Method
    """
    DEFINED_INTERVAL = auto()
    EQUAL_INTERVAL = auto()
    MANUAL = auto()
    NATURAL_BREAKS = auto()
    QUANTILE = auto()
    STANDARD_DEVIATION = auto()
    UNIQUE_VALUES = auto()
# End ReclassificationMethod class


class StandardDeviationOptions(StrEnum):
    """
    Standard Deviation Options
    """
    ONE = auto()
    HALF = auto()
    THIRD = auto()
    QUARTER = auto()
# End StandardDeviationOptions class


DEFAULT_GEOM_CHECKS: GeometryCheck = (
    GeometryCheck.EXTENT | GeometryCheck.EMPTY | GeometryCheck.EMPTY_PART |
    GeometryCheck.EMPTY_RING | GeometryCheck.EMPTY_POINT |
    GeometryCheck.NAN_Z | GeometryCheck.NAN_M |
    GeometryCheck.REPEATED_XY | GeometryCheck.REPEATED_M |
    GeometryCheck.MISMATCH_Z | GeometryCheck.MISMATCH_M
)
ALL_GEOM_CHECKS: GeometryCheck = (
    DEFAULT_GEOM_CHECKS | GeometryCheck.ORIENTATION | GeometryCheck.UNCLOSED |
    GeometryCheck.SELF_INTERSECTION | GeometryCheck.OUTSIDE_RING |
    GeometryCheck.OVERLAP_RING | GeometryCheck.POINT_COUNT)


if __name__ == '__main__':  # pragma: no cover
    pass
