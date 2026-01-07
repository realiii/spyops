# -*- coding: utf-8 -*-
"""
Enumerations
"""


from enum import StrEnum, auto


class Setting(StrEnum):
    """
    Analysis Settings
    """
    OVERWRITE = auto()

    XY_TOLERANCE = auto()
    OUTPUT_Z_FLAG = auto()
    Z_VALUE = auto()
    OUTPUT_M_FLAG = auto()

    CURRENT_WORKSPACE = auto()
    SCRATCH_WORKSPACE = auto()
# End Setting class


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


class OutputZOption(StrEnum):
    """
    Output Z Option
    """
    SAME = auto()
    ENABLED = auto()
    DISABLED = auto()
# End OutputZOption class


class OutputMOption(StrEnum):
    """
    Output M Option
    """
    SAME = auto()
    ENABLED = auto()
    DISABLED = auto()
# End OutputMOption class


if __name__ == '__main__':  # pragma: no cover
    pass
