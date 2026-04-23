# -*- coding: utf-8 -*-
"""
Package Initialization
"""


from spyops.analysis.extract import (
    clip, extract_features, extract_rows,
    select, split, split_by_attributes, table_select)
from spyops.analysis.overlay import (
    erase, intersect, symmetrical_difference, union)
from spyops.analysis.proximity import (
    buffer, create_thiessen_polygons,
    multiple_buffer)
from spyops.crs.enumeration import DistanceUnit
from spyops.crs.unit import (
    DecimalDegrees, Degrees, Feet, FeetInternational, FeetUS, Kilometers,
    Kilometres, Meters, Metres, Miles, MilesInternational, MilesUS,
    NauticalMiles, NauticalMilesInternational, NauticalMilesUS, StatuteMiles,
    USNauticalMiles, USSurveyFeet, USSurveyMiles, USSurveyYards, Yards,
    YardsInternational, YardsUS)
from spyops.shared.enumeration import (
    AlgorithmOption, AttributeOption, BufferTypeOption, DissolveOption,
    EndOption, OutputTypeOption, SideOption)


__all__ = [
    'clip',
    'extract_features',
    'extract_rows',
    'select',
    'split',
    'split_by_attributes',
    'table_select',

    'erase',
    'intersect',
    'symmetrical_difference',
    'union',

    'buffer',
    'create_thiessen_polygons',
    'multiple_buffer',

    'AlgorithmOption',
    'AttributeOption',
    'BufferTypeOption',
    'DissolveOption',
    'EndOption',
    'OutputTypeOption',
    'SideOption',

    'DistanceUnit',

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
