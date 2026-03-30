# -*- coding: utf-8 -*-
"""
Extraction
"""


from typing import Callable, TYPE_CHECKING, Union

from fudgeo import FeatureClass, MemoryGeoPackage

from spyops.analysis.util import _clip, _split_by_attributes
from spyops.query.analysis.extract import QuerySelect, QuerySplit
from spyops.shared.constant import UNDERSCORE
from spyops.shared.keywords import FIELD, GROUP_FIELDS, OPERATOR, SOURCE, TARGET
from spyops.shared.element import copy_element
from spyops.shared.field import GEOM_TYPE_POLYGONS, TEXTS, TEXT_AND_NUMBERS
from spyops.shared.hint import ELEMENT, FIELDS, FIELD_NAMES, GPKG, XY_TOL
from spyops.shared.records import select_and_transform_features
from spyops.shared.util import make_valid_name
from spyops.validation import (
    validate_element, validate_feature_class, validate_field,
    validate_geometry_dimension, validate_geopackage,
    validate_operator_feature_class, validate_overwrite_input,
    validate_overwrite_source, validate_result, validate_supported_crs,
    validate_source_feature_class, validate_table,
    validate_target_feature_class, validate_target_table, validate_xy_tolerance)


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import Field, Table


__all__ = ['table_select', 'select', 'extract_rows', 'extract_features',
           'split_by_attributes', 'clip', 'split']


@validate_result()
@validate_table(SOURCE)
@validate_target_table()
@validate_overwrite_source()
def table_select(source: 'Table', target: 'Table', *,
                 where_clause: str = '') -> 'Table':
    """
    Table Select

    Select rows from a table using a where clause (optional) and write results
    to a target table.
    """
    # noinspection PyTypeChecker
    return copy_element(source=source, target=target, where_clause=where_clause)
# End table_select function


@validate_result()
@validate_source_feature_class()
@validate_target_feature_class()
@validate_overwrite_source()
def select(source: FeatureClass, target: FeatureClass, *,
           where_clause: str = '') -> FeatureClass:
    """
    Select

    Select features from a feature class using a where clause (optional) and
    write results to a target feature class.
    """
    query = QuerySelect(source, target=target, where_clause=where_clause)
    return select_and_transform_features(query)
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
@validate_source_feature_class()
@validate_operator_feature_class()
@validate_target_feature_class()
@validate_xy_tolerance()
@validate_geometry_dimension(SOURCE, OPERATOR)
@validate_supported_crs(SOURCE, OPERATOR)
@validate_overwrite_input(TARGET, SOURCE, OPERATOR)
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
@validate_source_feature_class()
@validate_feature_class(OPERATOR, geometry_types=GEOM_TYPE_POLYGONS)
@validate_field(FIELD, data_types=TEXTS, single=True, element_name=OPERATOR)
@validate_geopackage()
@validate_xy_tolerance()
@validate_supported_crs(SOURCE, OPERATOR)
def split(source: FeatureClass, operator: FeatureClass,
          field: Union['Field', str], geopackage: GPKG, *,
          xy_tolerance: XY_TOL = None) -> list[FeatureClass]:
    """
    Split

    Extracts features for each polygon in the operator feature class and uses
    values from the specified field to name the output feature classes.
    """
    features = []
    query = QuerySplit(source, target=None, operator=operator,
                       xy_tolerance=xy_tolerance)
    if not query.has_intersection:
        return features
    scratch = MemoryGeoPackage.create()
    # noinspection PyTypeChecker
    splitters = _split_by_attributes(
        source=operator, group_fields=[field], geopackage=scratch,
        ignore_zm_settings=True)
    for (value,), s in splitters.items():
        name = make_valid_name(
            f'{source.name}{UNDERSCORE}{value}', prefix='split')
        # NOTE raw xy_tolerance used, avoid repeated conversion
        # noinspection PyTypeChecker
        target = _clip(
            source=source, operator=s, xy_tolerance=xy_tolerance,
            target=FeatureClass(geopackage=geopackage, name=name))
        features.append(target)
    if conn := scratch.connection:
        conn.close()
    return features
# End split function


# Aliases
extract_rows: Callable[['Table', 'Table', str, bool], 'Table'] = table_select
extract_features: Callable[[FeatureClass, FeatureClass, str, bool], FeatureClass] = select


if __name__ == '__main__':  # pragma: no cover
    pass
