# -*- coding: utf-8 -*-
"""
Data Management for Features
"""


from typing import Callable, TYPE_CHECKING

from fudgeo.constant import FETCH_SIZE
from fudgeo.context import ExecuteMany

from spyops.geometry.util import filter_features, to_shapely
from spyops.query.management.features import (
    QueryAddXYCoordinates, QueryCopyFeatures, QueryMultiPartToSinglePart)
from spyops.shared.constant import SOURCE, WEIGHT_OPTION
from spyops.shared.enumeration import WeightOption
from spyops.shared.field import GEOM_TYPE_MULTI
from spyops.shared.hint import ELEMENT
from spyops.shared.records import insert_many, select_and_transform_features
from spyops.validation import (
    validate_element, validate_enumeration, validate_feature_class,
    validate_overwrite_source, validate_result, validate_source_feature_class,
    validate_target_feature_class)


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass


__all__ = ['multipart_to_singlepart', 'explode', 'delete_features',
           'copy_features', 'add_xy_coordinates']


@validate_result()
@validate_feature_class(SOURCE, geometry_types=GEOM_TYPE_MULTI)
@validate_target_feature_class()
@validate_overwrite_source()
def multipart_to_singlepart(source: 'FeatureClass',
                            target: 'FeatureClass') -> 'FeatureClass':
    """
    MultiPart to Single Part

    Generates a feature class with single-part geometries by splitting
    multipart input features.  A column named ORIG_FID is added to the output
    feature class to track the original feature identifier.
    """
    parts = []
    records = []
    query = QueryMultiPartToSinglePart(source, target=target)
    insert_sql = query.insert
    getter = query.part_getter
    config = query.geometry_config
    transformer = query.source_transformer
    with (query.target.geopackage.connection as cout,
          query.source.geopackage.connection as cin,
          ExecuteMany(connection=cout, table=target) as executor):
        cursor = cin.execute(query.select)
        while features := cursor.fetchmany(FETCH_SIZE):
            if not (features := filter_features(features)):
                continue
            for geom, *attrs in features:
                parts.extend([(g, *attrs) for g in getter(geom)])
            insert_many(config, executor=executor, transformer=transformer,
                        insert_sql=insert_sql, features=parts, records=records)
            parts.clear()
    return query.target
# End multipart_to_singlepart function


@validate_result()
@validate_element(SOURCE, has_content=False)
def delete_features(source: ELEMENT, *, where_clause: str = '') -> ELEMENT:
    """
    Delete rows from a Table or Feature Class

    Deletes rows from a table or feature class using a where clause (optional).
    """
    source.delete(where_clause=where_clause)
    return source
# End delete_features function


@validate_result()
@validate_source_feature_class()
@validate_target_feature_class()
@validate_overwrite_source()
def copy_features(source: 'FeatureClass', target: 'FeatureClass', *,
                  where_clause: str = '') -> 'FeatureClass':
    """
    Copy Features

    Copies features from one feature class to another.  Optionally, select
    features using a where clause.
    """
    query = QueryCopyFeatures(source, target=target, where_clause=where_clause)
    return select_and_transform_features(query)
# End copy_features function


@validate_result()
@validate_source_feature_class()
@validate_enumeration(WEIGHT_OPTION, WeightOption)
def add_xy_coordinates(source: 'FeatureClass', *,
                       weight_option: WeightOption = WeightOption.TWO_D) \
        -> 'FeatureClass':
    """
    Add XY Coordinates

    Adds POINT_X and POINT_Y fields to a feature class.  Adds a POINT_Z field
    when the feature class is Z enabled and POINT_M field when the feature
    class is M enabled.  If the feature class already contains
    these fields, then the values in these fields will be updated.

    XY and Z values will be in the coordinate system of the feature class or
    the output coordinate system when set.
    """
    with QueryAddXYCoordinates(source, weight_option) as query:
        query_insert = query.insert
        getter = query.centroid_getter
        transformer = query.source_transformer
        with query.source.geopackage.connection as cin:
            cursor = cin.execute(query.select)
            while features := cursor.fetchmany(FETCH_SIZE):
                if not (features := filter_features(features)):
                    continue
                features, geometries = to_shapely(
                    features, transformer=transformer)
                records = [(i, *c) for (_, i), c in
                           zip(features, getter(geometries))]
                cin.executemany(query_insert, records)
            cin.execute(query.update)
    return query.target
# End add_xy_coordinates function


explode: Callable[['FeatureClass', 'FeatureClass'], 'FeatureClass'] = multipart_to_singlepart


if __name__ == '__main__':  # pragma: no cover
    pass
