# -*- coding: utf-8 -*-
"""
Enumerations
"""


from enum import StrEnum, auto


class DimensionOption(StrEnum):
    """
    Dimension Option
    """
    SAME = auto()
    TWO_D = auto()
    THREE_D = auto()
# End DimensionOption class


class GeometryInvalidReason(StrEnum):
    """
    Geometry Invalid Reason
    """
    BAD_EXTENT = auto()

    EMPTY = auto()
    NAN_Z = auto()
    NAN_M = auto()

    REPEATED_M = auto()
    NON_MONOTONIC = auto()

    EMPTY_POINT = auto()
    EMPTY_PART = auto()

    REPEATED_VERTICES = auto()

    MISMATCH_Z = auto()
    MISMATCH_M = auto()

    SELF_INTERSECTION = auto()

    UNCLOSED = auto()
    UNCLOSED_RING = auto()
    EMPTY_RING = auto()
    EXTERIOR_ORIENTATION = auto()
    INTERIOR_ORIENTATION = auto()
# End GeometryInvalidReason class


if __name__ == '__main__':  # pragma: no cover
    pass
