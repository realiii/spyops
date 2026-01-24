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


class CoordinateSystemNotSupportedError(OperationsError):
    """
    Coordinate System Not Supported Error
    """
# End CoordinateSystemNotSupportedError class


class NoValidTransformerError(BaseError):
    """
    No Valid Transformation Exists
    """
# End NoValidTransformerError class


class InvalidAreaOfInterestError(BaseError):
    """
    Invalid or Inappropriate AOI Error
    """
# End InvalidAreaOfInterestError class


if __name__ == '__main__':  # pragma: no cover
    pass
