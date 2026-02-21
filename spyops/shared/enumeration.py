# -*- coding: utf-8 -*-
"""
Enumerations
"""


from enum import StrEnum, auto


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


if __name__ == '__main__':  # pragma: no cover
    pass
