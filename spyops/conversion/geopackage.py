# -*- coding: utf-8 -*-
"""
To GeoPackage
"""


from typing import TYPE_CHECKING

from fudgeo import FeatureClass
from fudgeo.constant import FETCH_SIZE
from fudgeo.context import ExecuteMany

from spyops.environment import OutputMOption, OutputZOption, Setting
from spyops.environment.context import Swap
from spyops.query.conversion.geopackage import (
    QueryExportFeatures, QueryExportTable, QueryFeatureClassToGeoPackage,
    QueryTableToGeoPackage)
from spyops.shared.hint import (
    ELEMENT, ELEMENTS, FEATURE_CLASSES, GPKG, SORT_FIELDS)
from spyops.shared.keywords import SORT_FIELDS_ARG, SOURCE
from spyops.shared.records import select_and_transform_features
from spyops.validation import (
    validate_elements, validate_feature_classes, validate_geopackage,
    validate_overwrite_source, validate_result, validate_sort_field,
    validate_source_feature_class, validate_source_table,
    validate_target_feature_class, validate_target_table)


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import Table


__all__ = ['table_to_geopackage', 'feature_class_to_geopackage',
           'export_table', 'export_features']


@validate_result()
@validate_elements(SOURCE, has_content=False)
@validate_geopackage()
def table_to_geopackage(source: ELEMENTS, geopackage: GPKG) -> list[ELEMENT]:
    """
    Table to GeoPackage

    Copy one or more tables into a GeoPackage.
    """
    results = []
    with (Swap(Setting.OUTPUT_COORDINATE_SYSTEM, None),
          Swap(Setting.GEOGRAPHIC_TRANSFORMATIONS, []),
          Swap(Setting.EXTENT, None), Swap(Setting.Z_VALUE, None),
          Swap(Setting.OUTPUT_M_OPTION, OutputMOption.SAME),
          Swap(Setting.OUTPUT_Z_OPTION, OutputZOption.SAME)):
        for element in source:
            query = QueryTableToGeoPackage(element, geopackage=geopackage)
            results.append(query.copy())
    return results
# End table_to_geopackage function


@validate_result()
@validate_feature_classes(SOURCE, has_content=False)
@validate_geopackage()
def feature_class_to_geopackage(source: FEATURE_CLASSES,
                                geopackage: GPKG) -> list['FeatureClass']:
    """
    Feature Class to GeoPackage

    Copy one or more feature classes into a GeoPackage.
    """
    results = []
    for element in source:
        query = QueryFeatureClassToGeoPackage(element, geopackage=geopackage)
        results.append(query.copy())
    return results
# End feature_class_to_geopackage function


@validate_result()
@validate_source_table()
@validate_target_table()
@validate_sort_field(SORT_FIELDS_ARG, element_name=SOURCE)
@validate_overwrite_source()
def export_table(source: 'Table', target: 'Table', *, where_clause: str = '',
                 sort_fields: SORT_FIELDS = ()) -> 'Table':
    """
    Export Table

    Export rows from a table to a new table optionally using a where clause
    and sorting the rows.
    """
    # noinspection PyTypeChecker
    query = QueryExportTable(
        source, target=target, where_clause=where_clause,
        sort_fields=sort_fields)
    query_select = query.select
    query_insert = query.insert
    with (query.target.geopackage.connection as cout,
          query.source.geopackage.connection as cin,
          ExecuteMany(connection=cout, table=query.target) as executor):
        cursor = cin.execute(query_select)
        while rows := cursor.fetchmany(FETCH_SIZE):
            executor(query_insert, rows)
    return query.target
# End export_table function


@validate_result()
@validate_source_feature_class()
@validate_target_feature_class()
@validate_sort_field(SORT_FIELDS_ARG, element_name=SOURCE)
@validate_overwrite_source()
def export_features(source: 'FeatureClass', target: 'FeatureClass', *,
                    where_clause: str = '',
                    sort_fields: SORT_FIELDS = ()) -> 'FeatureClass':
    """
    Export Features

    Export features from a feature class to a new feature class optionally
    using a where clause and sorting the features.
    """
    # noinspection PyTypeChecker
    query = QueryExportFeatures(
        source, target=target, where_clause=where_clause,
        sort_fields=sort_fields)
    return select_and_transform_features(query)
# End export_features function


if __name__ == '__main__':  # pragma: no cover
    pass
