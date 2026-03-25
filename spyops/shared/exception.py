# -*- coding: utf-8 -*-
"""
Exceptions
"""


class BaseWarning(Warning):
    """
    Base Warning
    """
# End BaseWarning class


class BaseError(BaseException):
    """
    Base Error
    """
# End BaseError class


class OperationsWarning(BaseWarning):
    """
    Operations Warning
    """
# End OperationsError class


class OperationsError(BaseError):
    """
    Operations Error
    """
# End OperationsError class


class OverwriteError(OperationsError):
    """
    Overwrite Error
    """
# End OverwriteError class


class GeometryDimensionError(OperationsError):
    """
    Geometry Dimension Error
    """
# End GeometryDimensionError class


class CoordinateSystemNotSupportedError(OperationsError):
    """
    Coordinate System Not Supported Error
    """
# End CoordinateSystemNotSupportedError class


class CoordinateSystemDifferentError(OperationsError):
    """
    Coordinate System Different Error
    """
# End CoordinateSystemDifferentError class


class CoordinateSystemNotSupportedWarning(OperationsWarning):
    """
    Coordinate System Not Supported Warning
    """
# End CoordinateSystemNotSupportedWarning class


class NoValidTransformerError(OperationsError):
    """
    No Valid Transformation Exists
    """
# End NoValidTransformerError class


class InvalidAreaOfInterestError(OperationsError):
    """
    Invalid or Inappropriate AOI Error
    """
# End InvalidAreaOfInterestError class


class BadExtentWarning(OperationsWarning):
    """
    Bad Extent Warning
    """
# End BadExtentWarning class


class BadExtentError(OperationsError):
    """
    Bad Extent Error
    """
# End BadExtentError class


class ShapelyWarning(OperationsWarning):
    """
    Shapely Warning
    """
# End ShapelyWarning class


class NoResultWarning(OperationsWarning):
    """
    No Result Warning
    """
# End NoResultWarning class


class EmptyResultWarning(OperationsWarning):
    """
    Empty Result Warning
    """
# End EmptyResultWarning class


class TransformationGuessWarning(OperationsWarning):
    """
    Transformation Guess Warning
    """
# End TransformationGuessWarning class


class UnitParseWarning(OperationsWarning):
    """
    Unit Parse Warning
    """
# End UnitParseWarning class


class DistanceCalculationWarning(OperationsWarning):
    """
    Distance Calculation Warning
    """
# End DistanceCalculationWarning class


if __name__ == '__main__':  # pragma: no cover
    pass
