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


if __name__ == '__main__':  # pragma: no cover
    pass
