# -*- coding: utf-8 -*-
"""
Internal functions for analysis module
"""


from collections import defaultdict
from typing import Callable, TYPE_CHECKING, TypeAlias, Union

from fudgeo import FeatureClass
from fudgeo.constant import FETCH_SIZE
from fudgeo.context import ExecuteMany
from numpy import concatenate
from shapely import STRtree, difference

from spyops.environment import ANALYSIS_SETTINGS
from spyops.environment.context import Swap
from spyops.environment.core import zm_config
from spyops.environment.enumeration import (
    OutputMOption, OutputZOption, Setting)
from spyops.geometry.config import geometry_config
from spyops.geometry.multi import build_multi
from spyops.geometry.util import filter_features, to_shapely
from spyops.geometry.validate import get_validated_geometries
from spyops.geometry.wa import set_precision
from spyops.query.analysis.extract import QueryClip, QuerySplitByAttributes
from spyops.shared.constant import SQL_EMPTY, UNDERSCORE
from spyops.shared.element import copy_element
from spyops.shared.hint import (
    ELEMENT, FIELDS, FIELD_NAMES, GPKG, GRID_SIZE, XY_TOL)
from spyops.shared.records import bulk_insert, extend_records
from spyops.shared.util import (
    element_names, make_unique_name, make_valid_name)


if TYPE_CHECKING:  # pragma: no cover
    from numpy import ndarray
    from spyops.geometry.config import GeometryConfig
    from spyops.query.analysis.overlay import (
        QueryIntersectClassic, QueryIntersectPairwise,
        QuerySymmetricalDifferenceClassic, QuerySymmetricalDifferencePairwise)


QUERY_INT: TypeAlias = Union['QueryIntersectClassic', 'QueryIntersectPairwise']
QUERY_SYM: TypeAlias = Union['QuerySymmetricalDifferenceClassic', 'QuerySymmetricalDifferencePairwise']


def _clip(*, source: FeatureClass, operator: FeatureClass,
          target: FeatureClass, xy_tolerance: XY_TOL) -> FeatureClass:
    """
    Internal Clip
    """
    query = QueryClip(source=source, target=target, operator=operator,
                      xy_tolerance=xy_tolerance)
    if not query.has_intersection:
        return query.target_empty
    records = []
    insert_sql = query.insert
    geometry = query.geometry
    grid_size = query.grid_size
    config = query.geometry_config
    transformer = query.source_transformer
    with (query.target.geopackage.connection as cout,
          query.source.geopackage.connection as cin,
          ExecuteMany(connection=cout, table=query.target) as executor):
        cursor = cin.execute(query.select)
        while features := cursor.fetchmany(FETCH_SIZE):
            if not (features := filter_features(features)):
                continue
            features, geometries = to_shapely(features, transformer=transformer)
            intersects = geometry.intersects(geometries)
            if not intersects.any():
                continue
            keepers = [f for f, has_intersection in zip(features, intersects)
                       if has_intersection]
            geoms = geometry.intersection(
                geometries[intersects], grid_size=grid_size)
            results = [(g, attrs) for g, (_, *attrs) in zip(geoms, keepers)]
            extend_records(results, records=records, config=config)
            executor(sql=insert_sql, data=records)
            records.clear()
    return query.target
# End _clip function


def _split_by_attributes(*, source: ELEMENT, group_fields: FIELDS | FIELD_NAMES,
                         geopackage: GPKG, ignore_zm_settings: bool) \
        -> dict[tuple, ELEMENT]:
    """
    Internal Split by Attributes
    """
    elements = {}
    is_feature_class = isinstance(source, FeatureClass)
    cls = source.__class__
    target_names = element_names(geopackage)
    query = QuerySplitByAttributes(element=source, fields=group_fields)
    query_select = query.select
    query_insert = query.insert
    source_name = query.source.name
    if ignore_zm_settings:
        z_option = OutputZOption.SAME
        m_option = OutputMOption.SAME
    else:
        z_option = ANALYSIS_SETTINGS.output_z_option
        m_option = ANALYSIS_SETTINGS.output_m_option
    with (geopackage.connection as cout,
          query.source.geopackage.connection as cin,
          Swap(Setting.OUTPUT_Z_OPTION, z_option),
          Swap(Setting.OUTPUT_M_OPTION, m_option)):
        if is_feature_class:
            is_different = zm_config(source).is_different
            transformer = query.source_transformer
        else:
            is_different = False
            transformer = None
        cursor = cin.execute(query.groups)
        groups = cursor.fetchall()
        for i, *group in groups:
            name = UNDERSCORE.join([str(g).strip() for g in group])
            name = make_valid_name(name, prefix=source_name)
            name = make_unique_name(name, names=target_names)
            element = copy_element(
                source=source, where_clause=SQL_EMPTY,
                target=cls(geopackage=geopackage, name=name))
            elements[tuple(group)] = element
            cursor = cin.execute(query_select, (i,))
            insert_sql = query_insert.format(element.escaped_name)
            with ExecuteMany(connection=cout, table=element) as executor:
                if is_feature_class:
                    config = geometry_config(element, cast_geom=is_different)
                    bulk_insert(cursor, config=config, executor=executor,
                                transformer=transformer, insert_sql=insert_sql)
                else:
                    while records := cursor.fetchmany(FETCH_SIZE):
                        executor(sql=insert_sql, data=records)
    return elements
# End _split_by_attributes function


def _difference(*, source: FeatureClass, source_transformer: Callable | None,
                select_sql: str, insert_sql: str,
                overlay_geoms: 'ndarray', overlay_transformer: Callable | None,
                target: FeatureClass, config: 'GeometryConfig',
                grid_size: GRID_SIZE) -> None:
    """
    Internal Difference
    """
    records = []
    tree = STRtree(overlay_geoms)
    with (target.geopackage.connection as cout,
          source.geopackage.connection as cin,
          ExecuteMany(connection=cout, table=target) as executor):
        cursor = cin.execute(select_sql)
        while features := cursor.fetchmany(FETCH_SIZE):
            if not (features := filter_features(features)):
                continue
            features, geometries = to_shapely(
                features, transformer=source_transformer)
            intersects = tree.query(geometries, predicate='intersects')
            if not len(intersects):
                results = [(g, attr) for g, (_, *attr) in
                           zip(geometries, features)]
                extend_records(results, records=records, config=config)
                executor(sql=insert_sql, data=records)
                records.clear()
                continue
            change_indexes, indexes = intersects
            change_indexes = set(change_indexes)
            keeper_indexes = list(set(range(len(geometries))) - change_indexes)
            keepers = [features[i] for i in keeper_indexes]
            geoms = geometries[keeper_indexes]
            if grid_size is not None:
                geoms = set_precision(geoms, grid_size=grid_size)
            results = [(geom, attrs) for geom, (_, *attrs) in
                       zip(geoms, keepers)]
            extend_records(results, records=records, config=config)

            overlay = build_multi(
                overlay_geoms[list(set(indexes))],
                transformer=overlay_transformer, select_sql=None)
            change_indexes = list(change_indexes)
            changers = [features[i] for i in change_indexes]
            differences = difference(
                geometries[change_indexes], overlay, grid_size=grid_size)
            results = [(geom, attrs) for geom, (_, *attrs) in
                       zip(differences, changers)]
            extend_records(results, records=records, config=config)

            executor(sql=insert_sql, data=records)
            records.clear()
# End _difference function


def _symmetrical_difference(query: QUERY_SYM) -> None:
    """
    Internal Symmetrical Difference
    """
    geoms = get_validated_geometries(
        query.operator, select_sql=query.select_operator,
        transformer=query.operator_transformer)
    _difference(
        source=query.source, source_transformer=query.source_transformer,
        select_sql=query.select_source, insert_sql=query.source_config.insert,
        overlay_geoms=geoms, overlay_transformer=query.operator_transformer,
        target=query.target, config=query.geometry_config,
        grid_size=query.grid_size)
    geoms = get_validated_geometries(
        query.source, select_sql=query.select_source,
        transformer=query.source_transformer)
    _difference(
        source=query.operator, source_transformer=query.operator_transformer,
        select_sql=query.select_operator, insert_sql=query.operator_config.insert,
        overlay_geoms=geoms, overlay_transformer=query.source_transformer,
        target=query.target, config=query.geometry_config,
        grid_size=query.grid_size)
# End _symmetrical_difference function


def _get_converted_operator(*, query: QUERY_INT, converter: Callable,
                            transformer: Callable | None) \
        -> tuple[list[tuple], 'ndarray']:
    """
    Get Converted Operator Features and Geometries
    """
    op_geoms = []
    op_features = []
    with query.operator.geopackage.connection as cin:
        cursor = cin.execute(query.select_operator)
        while features := cursor.fetchmany(FETCH_SIZE):
            if not (features := filter_features(features)):
                continue
            features, geometries = to_shapely(features, transformer=transformer)
            op_features.extend(features)
            op_geoms.append(geometries)
    return op_features, converter(concatenate(op_geoms))
# End _get_converted_operator function


def _intersect(*, query: QUERY_INT, op_features: list[tuple],
               op_geoms: 'ndarray', src_convert: Callable) -> FeatureClass:
    """
    Internal Intersect
    """
    records = []
    tree = STRtree(op_geoms)
    insert_sql = query.insert
    grid_size = query.grid_size
    config = query.geometry_config
    transformer = query.source_transformer
    with (query.target.geopackage.connection as cout,
          query.source.geopackage.connection as cin,
          ExecuteMany(connection=cout, table=query.target) as executor):
        cursor = cin.execute(query.select)
        while features := cursor.fetchmany(FETCH_SIZE):
            if not (features := filter_features(features)):
                continue
            features, geometries = to_shapely(features, transformer=transformer)
            geometries = src_convert(geometries)
            intersects = tree.query(geometries, predicate='intersects')
            if not len(intersects):
                continue
            grouper = defaultdict(list)
            for src_idx, op_idx in intersects.T.tolist():
                grouper[op_idx].append(src_idx)
            results = []
            for op_idx, indexes in grouper.items():
                op_attr = op_features[op_idx][1:]
                op_geom = op_geoms[op_idx]
                src_attrs = [features[idx][1:] for idx in indexes]
                intersections = op_geom.intersection(
                    geometries[indexes], grid_size=grid_size)
                results.extend([
                    (g, (*src_attr, *op_attr))
                    for g, src_attr in zip(intersections, src_attrs)])
            extend_records(results, records=records, config=config)
            executor(sql=insert_sql, data=records)
            records.clear()
    return query.target
# End _intersect function


if __name__ == '__main__':  # pragma: no cover
    pass
