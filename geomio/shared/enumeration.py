# -*- coding: utf-8 -*-
"""
Enumerations
"""


from enum import StrEnum, auto


class InfoOption(StrEnum):
    """
    Coordinate Reference System Information Options
    """
    ORIGINAL = auto()
    HORIZONTAL = auto()
    VERTICAL = auto()
# End InfoOption class


class Setting(StrEnum):
    """
    Analysis Settings
    """
    OVERWRITE = auto()
    XY_TOLERANCE = auto()

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


if __name__ == '__main__':  # pragma: no cover
    pass
