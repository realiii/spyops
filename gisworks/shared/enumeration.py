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
    Algorithm Option
    """
    CLASSIC = auto()
    PAIRWISE = auto()
# End AlgorithmOption class


class OutputTypeOption(StrEnum):
    """
    Output Type Option
    """
    SAME = auto()
    LINE = auto()
    POINT = auto()
# End OutputTypeOption class


if __name__ == '__main__':  # pragma: no cover
    pass
