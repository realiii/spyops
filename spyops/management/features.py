# -*- coding: utf-8 -*-
"""
Data Management for Features
"""


from typing import Callable, TYPE_CHECKING

from fudgeo.constant import FETCH_SIZE
from fudgeo.context import ExecuteMany

from spyops.geometry.util import filter_features
from spyops.query.management.features import (
    QueryCopyFeatures, QueryMultiPartToSinglePart)
from spyops.shared.constant import SOURCE, TARGET
from spyops.shared.field import GEOM_TYPE_MULTI
from spyops.shared.hint import ELEMENT
from spyops.shared.records import insert_many, select_and_transform_features
from spyops.validation import (
    validate_element, validate_feature_class, validate_overwrite_input,
    validate_overwrite_source, validate_result, validate_source_feature_class,
    validate_target_feature_class)


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass


__all__ = ['multipart_to_singlepart', 'explode', 'delete_features',
           'copy_features']


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


explode: Callable[['FeatureClass', 'FeatureClass'], 'FeatureClass'] = multipart_to_singlepart


if __name__ == '__main__':  # pragma: no cover
    pass
