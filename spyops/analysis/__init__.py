# -*- coding: utf-8 -*-
"""
Package Initialization
"""


from spyops.analysis.extract import (
    clip, extract_features, extract_rows,
    select, split, split_by_attributes, table_select)
from spyops.analysis.overlay import (
    erase, intersect, symmetrical_difference, union)
from spyops.analysis.proximity import buffer
from spyops.crs.unit import (
    DecimalDegrees, Degrees, Feet, FeetInternational, FeetUS, Kilometers,
    Kilometres, Meters, Metres, Miles, MilesInternational, MilesUS,
    NauticalMiles, NauticalMilesInternational, NauticalMilesUS, StatuteMiles,
    USSurveyFeet, USSurveyMiles, USSurveyYards, Yards, YardsInternational,
    YardsUS)
from spyops.shared.enumeration import (
    AlgorithmOption, AttributeOption, BufferTypeOption, DissolveOption,
    EndOption, OutputTypeOption, SideOption)


__all__ = [
    'buffer',
    'clip',
    'erase',
    'extract_features',
    'extract_rows',
    'intersect',
    'select',
    'split',
    'split_by_attributes',
    'symmetrical_difference',
    'table_select',
    'union',

    'AlgorithmOption',
    'AttributeOption',
    'BufferTypeOption',
    'DissolveOption',
    'EndOption',
    'OutputTypeOption',
    'SideOption',

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
    'USSurveyFeet',
    'USSurveyMiles',
    'USSurveyYards',
    'Yards',
    'YardsInternational',
    'YardsUS',
]


if __name__ == '__main__':  # pragma: no cover
    pass
