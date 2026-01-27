# -*- coding: utf-8 -*-
"""
Environment / Analysis Settings Enumerations
"""


from enum import StrEnum, auto


class Setting(StrEnum):
    """
    Analysis Settings
    """
    OVERWRITE = auto()

    XY_TOLERANCE = auto()
    Z_VALUE = auto()
    OUTPUT_Z_OPTION = auto()
    OUTPUT_M_OPTION = auto()

    CURRENT_WORKSPACE = auto()
    SCRATCH_WORKSPACE = auto()
    SCRATCH_FOLDER = auto()

    OUTPUT_COORDINATE_SYSTEM = auto()
# End Setting class


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
