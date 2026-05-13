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
    buffer, create_thiessen_polygons, multiple_buffer)
from spyops.analysis.statistics import frequency, statistics
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
from spyops.shared.stats import (
    Average, Avg, CV, CoefficientOfVariation, Concat, Concatenate, Count,
    CountNonNull, CountNull, CountOutlier, First, FirstQuartile, IQR,
    InterquartileRange, Kurt, Kurtosis, Last, Least, LeastCommon, Max, Maximum,
    Mean, Median, Min, Minimum, Mode, Most, MostCommon, Outliers, Q1, Q3, Range,
    Skew, Skewness, StandardDeviation, StdDev, Sum, Summation, ThirdQuartile,
    Unique, Var, Variance, Variation)


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

    'frequency',
    'statistics',

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

    'Average',
    'Avg',
    'CV',
    'CoefficientOfVariation',
    'Concat',
    'Concatenate',
    'Count',
    'CountNonNull',
    'CountNull',
    'CountOutlier',
    'First',
    'FirstQuartile',
    'IQR',
    'InterquartileRange',
    'Kurt',
    'Kurtosis',
    'Last',
    'Least',
    'LeastCommon',
    'Max',
    'Maximum',
    'Mean',
    'Median',
    'Min',
    'Minimum',
    'Mode',
    'Most',
    'MostCommon',
    'Outliers',
    'Q1',
    'Q3',
    'Range',
    'Skew',
    'Skewness',
    'StandardDeviation',
    'StdDev',
    'Sum',
    'Summation',
    'ThirdQuartile',
    'Unique',
    'Var',
    'Variance',
    'Variation',
]


if __name__ == '__main__':  # pragma: no cover
    pass
