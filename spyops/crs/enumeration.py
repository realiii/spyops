# -*- coding: utf-8 -*-
"""
Enumerations for Coordinate Reference Systems
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


class LengthUnit(StrEnum):
    """
    Length Units
    """
    KILOMETERS = auto()
    METERS = auto()

    MILES_INTERNATIONAL = auto()
    NAUTICAL_MILES_INTERNATIONAL = auto()
    YARDS_INTERNATIONAL = auto()
    FEET_INTERNATIONAL = auto()

    STATUTE_MILES = auto()
    MILES = auto()
    YARDS = auto()
    FEET = auto()

    MILES_US = auto()
    NAUTICAL_MILES_US = auto()
    YARDS_US = auto()
    FEET_US = auto()

    US_SURVEY_MILES = auto()
    US_SURVEY_YARDS = auto()
    US_SURVEY_FEET = auto()
# End LengthUnit class


class AreaUnit(StrEnum):
    """
    Area Units
    """
    SQUARE_KILOMETERS = auto()
    SQUARE_METERS = auto()

    SQUARE_MILES_INTERNATIONAL = auto()
    SQUARE_NAUTICAL_MILES_INTERNATIONAL = auto()
    SQUARE_YARDS_INTERNATIONAL = auto()
    SQUARE_FEET_INTERNATIONAL = auto()

    SQUARE_MILES_US = auto()
    SQUARE_NAUTICAL_MILES_US = auto()
    SQUARE_YARDS_US = auto()
    SQUARE_FEET_US = auto()

    HECTARES = auto()
    ACRES_INTERNATIONAL = auto()
    ACRES_US = auto()
# End AreaUnit class


if __name__ == '__main__':  # pragma: no cover
    pass
