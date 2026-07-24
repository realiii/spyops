# -*- coding: utf-8 -*-
"""
Package Initialization
"""


from spyops.cartography.generalization import simplify_line, simplify_polygon
from spyops.crs.unit import (
    DecimalDegrees, Degrees, Feet, FeetInternational, FeetUS, Kilometers,
    Kilometres, Meters, Metres, Miles, MilesInternational, MilesUS,
    NauticalMiles, NauticalMilesInternational, NauticalMilesUS, StatuteMiles,
    USNauticalMiles, USSurveyFeet, USSurveyMiles, USSurveyYards, Yards,
    YardsInternational, YardsUS)
from spyops.shared.enumeration import SimplifyAlgorithmOption


__all__ = [
    'simplify_line',
    'simplify_polygon',

    'SimplifyAlgorithmOption',

    'DecimalDegrees',
    'Degrees',
    'Feet',
    'FeetInternational',
    'FeetUS',
    'Kilometers',
    'Kilometres',
    'Meters',
    'Metres',
    'Miles',
    'MilesInternational',
    'MilesUS',
    'NauticalMiles',
    'NauticalMilesInternational',
    'NauticalMilesUS',
    'StatuteMiles',
    'USNauticalMiles',
    'USSurveyFeet',
    'USSurveyMiles',
    'USSurveyYards',
    'Yards',
    'YardsInternational',
    'YardsUS',
]


if __name__ == '__main__':  # pragma: no cover
    pass
