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


class Settings(StrEnum):
    """
    Analysis Settings
    """
    OVERWRITE = auto()
    XY_TOLERANCE = auto()
# End Settings class


if __name__ == '__main__':  # pragma: no cover
    pass
