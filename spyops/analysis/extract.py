# -*- coding: utf-8 -*-
"""
Extraction
"""


from typing import Callable

from fudgeo import FeatureClass, Field, Table

from spyops.analysis.util import _clip, _split_by_attributes
from spyops.environment import ANALYSIS_SETTINGS
from spyops.query.extract import QuerySplit
from spyops.shared.constant import (
    FIELD, GROUP_FIELDS, OPERATOR, SOURCE, TARGET, UNDERSCORE)
from spyops.shared.element import copy_element
from spyops.shared.field import GEOM_TYPE_POLYGONS, TEXTS, TEXT_AND_NUMBERS
from spyops.shared.hint import ELEMENT, FIELDS, FIELD_NAMES, GPKG, XY_TOL
from spyops.shared.util import make_valid_name
from spyops.validation import (
    validate_element, validate_feature_class, validate_field,
    validate_geometry_dimension, validate_geopackage, validate_result,
    validate_same_crs, validate_table, validate_xy_tolerance)


__all__ = ['table_select', 'select', 'extract_rows', 'extract_features',
           'split_by_attributes', 'clip', 'split']


@validate_result()
@validate_table(SOURCE)
@validate_table(TARGET, exists=False)
def table_select(source: Table, target: Table, *,
                 where_clause: str = '') -> Table:
    """
    Table Select

    Select rows from a table using a where clause (optional) and write results
    to a target table.
    """
    return copy_element(source=source, target=target, where_clause=where_clause)
# End table_select function


@validate_result()
@validate_feature_class(SOURCE)
@validate_feature_class(TARGET, exists=False)
def select(source: FeatureClass, target: FeatureClass, *,
           where_clause: str = '') -> FeatureClass:
    """
    Select

    Select features from a feature class using a where clause (optional) and
    write results to a target feature class.
    """
    return copy_element(source=source, target=target, where_clause=where_clause)
# End select function


@validate_result()
@validate_element(SOURCE)
@validate_field(GROUP_FIELDS, data_types=TEXT_AND_NUMBERS,
                element_name=SOURCE, exclude_primary=False)
@validate_geopackage()
def split_by_attributes(source: ELEMENT, group_fields: FIELDS | FIELD_NAMES,
                        geopackage: GPKG) -> list[ELEMENT]:
    """
    Split by Attributes

    Split an input table or feature class by groups of attributes.
    """
    results = _split_by_attributes(
        source=source, group_fields=group_fields, geopackage=geopackage,
        ignore_zm_settings=False)
    return list(results.values())
# End split_by_attributes function


@validate_result()
@validate_feature_class(SOURCE)
@validate_feature_class(OPERATOR)
@validate_feature_class(TARGET, exists=False)
@validate_xy_tolerance()
@validate_geometry_dimension(SOURCE, OPERATOR)
@validate_same_crs(SOURCE, OPERATOR)
def clip(source: FeatureClass, operator: FeatureClass, target: FeatureClass, *,
         xy_tolerance: XY_TOL = None) -> FeatureClass:
    """
    Clip

    Extracts features using the features of a polygon feature class. Extracted
    features are cut along the edges of the operator polygons.
    """
    return _clip(source=source, operator=operator, target=target,
                 xy_tolerance=xy_tolerance)
# End clip function


@validate_result()
@validate_feature_class(SOURCE)
@validate_feature_class(OPERATOR, geometry_types=GEOM_TYPE_POLYGONS)
@validate_field(FIELD, data_types=TEXTS, single=True, element_name=OPERATOR)
@validate_geopackage()
@validate_xy_tolerance()
@validate_same_crs(SOURCE, OPERATOR)
def split(source: FeatureClass, operator: FeatureClass, field: Field | str,
          geopackage: GPKG, *, xy_tolerance: XY_TOL = None) -> list[FeatureClass]:
    """
    Split

    Extracts features for each polygon in the operator feature class and uses
    values from the specified field to name the output feature classes.
    """
    features = []
    query = QuerySplit(source, target=None, operator=operator)
    if not query.has_intersection:
        return features
    splitters = _split_by_attributes(
        source=operator, group_fields=[field],
        geopackage=ANALYSIS_SETTINGS.scratch_workspace,
        ignore_zm_settings=True)
    for (value,), s in splitters.items():
        name = make_valid_name(
            f'{source.name}{UNDERSCORE}{value}', prefix='split')
        target = _clip(
            source=source, operator=s, xy_tolerance=xy_tolerance,
            target=FeatureClass(geopackage=geopackage, name=name))
        features.append(target)
    return features
# End split function


# Aliases
extract_rows: Callable[[Table, Table, str, bool], Table] = table_select
extract_features: Callable[[FeatureClass, FeatureClass, str, bool], FeatureClass] = select


if __name__ == '__main__':  # pragma: no cover
    pass
