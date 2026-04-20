# -*- coding: utf-8 -*-
"""
Projections and Transformations
"""


from typing import TYPE_CHECKING

from fudgeo import SpatialReferenceSystem
from fudgeo.constant import FETCH_SIZE
from fudgeo.context import ExecuteMany
from pyproj import CRS
from pyproj.transformer import Transformer

from spyops.environment import OutputMOption, OutputZOption, Setting
from spyops.environment.context import Swap
from spyops.query.management.projections import (
    QueryDefineProjection, QueryProject)
from spyops.shared.keywords import COORDINATE_SYSTEM, TRANSFORM
from spyops.shared.records import insert_many, select_and_transform_features
from spyops.validation import (
    validate_coordinate_system, validate_overwrite_source, validate_result,
    validate_source_feature_class, validate_target_feature_class,
    validate_transform)


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass


__all__ = ['project', 'define_projection']


@validate_result()
@validate_source_feature_class()
@validate_target_feature_class()
@validate_coordinate_system(COORDINATE_SYSTEM)
@validate_transform(TRANSFORM)
@validate_overwrite_source()
def project(source: 'FeatureClass', target: 'FeatureClass', *,
            coordinate_system: CRS | SpatialReferenceSystem,
            transform: Transformer | None = None) -> 'FeatureClass':
    """
    Project

    Transform the features of a feature class into another coordinate system.
    Supports geographic and projected coordinate systems, also supports
    vertical coordinate systems.  The z values of z-aware features will be
    updated if the transform provided includes vertical transformation and the
    source coordinate system includes vertical component.

    This function ignores the settings for EXTENT, Z_VALUE, OUTPUT_Z_OPTION,
    and OUTPUT_M_OPTION. The input coordinate system and transform
    values are used to temporarily define Settings during internal processing.
    """
    with (Swap(Setting.EXTENT, None), Swap(Setting.Z_VALUE, None),
          Swap(Setting.OUTPUT_Z_OPTION, OutputZOption.SAME),
          Swap(Setting.OUTPUT_M_OPTION, OutputMOption.SAME),
          Swap(Setting.OUTPUT_COORDINATE_SYSTEM, coordinate_system),
          Swap(Setting.GEOGRAPHIC_TRANSFORMATIONS, transform)):
        query = QueryProject(source, target=target)
        target = select_and_transform_features(query)
    return target
# End project function


@validate_result()
@validate_source_feature_class()
@validate_target_feature_class()
@validate_coordinate_system(COORDINATE_SYSTEM)
@validate_overwrite_source()
def define_projection(source: 'FeatureClass', target: 'FeatureClass', *,
                      coordinate_system: CRS | SpatialReferenceSystem) \
        -> 'FeatureClass':
    """
    Define Projection

    Change the coordinate reference system for a feature class without changing
    any coordinate values.  The output spatial reference system will be the
    specified coordinate reference system.  The srs_id for each geometry is
    updated during this process.
    """
    records = []
    with (Swap(Setting.EXTENT, None), Swap(Setting.Z_VALUE, None),
          Swap(Setting.OUTPUT_Z_OPTION, OutputZOption.SAME),
          Swap(Setting.OUTPUT_M_OPTION, OutputMOption.SAME),
          Swap(Setting.OUTPUT_COORDINATE_SYSTEM, None),
          Swap(Setting.GEOGRAPHIC_TRANSFORMATIONS, None)):
        query = QueryDefineProjection(
            source, target=target, coordinate_system=coordinate_system)
        insert_sql = query.insert
        config = query.geometry_config
        transformer = query.source_transformer
        srs_id = query.spatial_reference_system.srs_id
        with (query.source.geopackage.connection as cin,
              query.target.geopackage.connection as cout,
              ExecuteMany(connection=cout, table=query.target) as executor):
            cursor = cin.execute(query.select)
            while features := cursor.fetchmany(FETCH_SIZE):
                for geom, *_ in features:
                    geom.srs_id = srs_id
                insert_many(config, executor=executor, transformer=transformer,
                            insert_sql=insert_sql, features=features,
                            records=records)
                records.clear()
    return query.target
# End define_projection function


if __name__ == '__main__':  # pragma: no cover
    pass
