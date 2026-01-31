# -*- coding: utf-8 -*-
"""
Internal functions for analysis module
"""


from collections import defaultdict
from typing import Callable, TYPE_CHECKING, TypeAlias, Union

from fudgeo import FeatureClass
from fudgeo.constant import FETCH_SIZE
from fudgeo.context import ExecuteMany
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
from spyops.shared.hint import ELEMENT, FIELDS, FIELD_NAMES, GPKG, XY_TOL
from spyops.shared.records import bulk_insert, extend_records
from spyops.shared.util import (
    element_names, make_unique_name, make_valid_name)


if TYPE_CHECKING:  # pragma: no cover
    from shapely.geometry.base import BaseGeometry
    from spyops.geometry.config import GeometryConfig
    from spyops.query.analysis.overlay import (
        QueryIntersectClassic, QueryIntersectPairwise,
        QuerySymmetricalDifferenceClassic, QuerySymmetricalDifferencePairwise)


QUERY_INT: TypeAlias = Union['QueryIntersectClassic', 'QueryIntersectPairwise']
QUERY_SYN: TypeAlias = Union['QuerySymmetricalDifferenceClassic', 'QuerySymmetricalDifferencePairwise']


def _clip(*, source: FeatureClass, operator: FeatureClass,
          target: FeatureClass, xy_tolerance: XY_TOL) -> FeatureClass:
    """
    Internal Clip
    """
    query = QueryClip(source=source, target=target, operator=operator)
    if not query.has_intersection:
        return query.target_empty
    records = []
    insert_sql = query.insert
    geometry = query.geometry
    config = query.geometry_config
    with (query.target.geopackage.connection as cout,
          query.source.geopackage.connection as cin,
          ExecuteMany(connection=cout, table=query.target) as executor):
        cursor = cin.execute(query.select)
        while features := cursor.fetchmany(FETCH_SIZE):
            if not (features := filter_features(features)):
                continue
            geometries = to_shapely(features)
            intersects = geometry.intersects(geometries)
            if not intersects.any():
                continue
            keepers = [f for f, keep in zip(features, intersects) if keep]
            geoms = geometry.intersection(
                [g for g, keep in zip(geometries, intersects) if keep],
                grid_size=xy_tolerance)
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
    target_names = element_names(geopackage)
    query = QuerySplitByAttributes(element=source, fields=group_fields)
    query_select = query.select
    query_insert = query.insert
    source_name = query.source.name
    transformer = query.transformer
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
        if isinstance(source, FeatureClass):
            is_different = zm_config(source).is_different
        else:
            is_different = False
        cursor = cin.execute(query.groups)
        groups = cursor.fetchall()
        for i, *group in groups:
            name = UNDERSCORE.join([str(g).strip() for g in group])
            name = make_valid_name(name, prefix=source_name)
            name = make_unique_name(name, names=target_names)
            element = copy_element(
                source=source, where_clause=SQL_EMPTY,
                target=FeatureClass(geopackage=geopackage, name=name))
            elements[tuple(group)] = element
            config = geometry_config(element, cast_geom=is_different)
            cursor = cin.execute(query_select, (i,))
            with ExecuteMany(connection=cout, table=element) as executor:
                insert_sql = query_insert.format(element.escaped_name)
                bulk_insert(cursor, config=config, executor=executor,
                            transformer=transformer, insert_sql=insert_sql)
    return elements
# End _split_by_attributes function


def _difference(*, source: FeatureClass, select_sql: str, insert_sql: str,
                overlay_geoms: list, target: FeatureClass,
                config: 'GeometryConfig', xy_tolerance: XY_TOL) -> None:
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
            geometries = to_shapely(features)
            intersects = tree.query(geometries, predicate='intersects')
            if not len(intersects):
                results = [(g, attr) for g, (_, *attr) in
                           zip(geometries, features)]
                extend_records(results, records=records, config=config)
                continue
            changer_indexes, indexes = intersects
            overlay = build_multi([overlay_geoms[i] for i in set(indexes)])
            changer_indexes = set(changer_indexes)
            keeper_indexes = set(range(len(geometries))) - changer_indexes
            keepers = [features[i] for i in keeper_indexes]
            geoms = [geometries[i] for i in keeper_indexes]
            if xy_tolerance is not None:
                geoms = set_precision(geoms, grid_size=xy_tolerance)
            results = [(geom, attrs) for geom, (_, *attrs) in
                       zip(geoms, keepers)]
            extend_records(results, records=records, config=config)
            changers = [features[i] for i in changer_indexes]
            geoms = [geometries[i] for i in changer_indexes]
            differences = difference(geoms, overlay, grid_size=xy_tolerance)
            results = [(geom, attrs) for geom, (_, *attrs) in
                       zip(differences, changers)]
            extend_records(results, records=records, config=config)
            executor(sql=insert_sql, data=records)
            records.clear()
# End _difference function


def _symmetrical_difference(*, query: QUERY_SYN, xy_tolerance: XY_TOL) -> None:
    """
    Internal Symmetrical Difference
    """
    geoms = get_validated_geometries(query.operator)
    _difference(source=query.source, select_sql=query.select_source,
                insert_sql=query.source_config.insert, overlay_geoms=geoms,
                target=query.target, config=query.geometry_config,
                xy_tolerance=xy_tolerance)
    geoms = get_validated_geometries(query.source)
    _difference(source=query.operator, select_sql=query.select_operator,
                insert_sql=query.operator_config.insert,
                overlay_geoms=geoms, target=query.target,
                config=query.geometry_config, xy_tolerance=xy_tolerance)
# End _symmetrical_difference function


def _get_converted_operator(*, query: QUERY_INT, converter: Callable) \
        -> tuple[list[tuple], list[BaseGeometry]]:
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
            op_features.extend(features)
            op_geoms.extend(to_shapely(features))
    return op_features, converter(op_geoms)
# End _get_converted_operator function


def _intersect(*, query: QUERY_INT, op_features: list[tuple],
               op_geoms: list[BaseGeometry], src_convert: Callable,
               xy_tolerance: XY_TOL) -> FeatureClass:
    """
    Internal Intersect
    """
    records = []
    tree = STRtree(op_geoms)
    insert_sql = query.insert
    config = query.geometry_config
    with (query.target.geopackage.connection as cout,
          query.source.geopackage.connection as cin,
          ExecuteMany(connection=cout, table=query.target) as executor):
        cursor = cin.execute(query.select)
        while features := cursor.fetchmany(FETCH_SIZE):
            if not (features := filter_features(features)):
                continue
            geometries = src_convert(to_shapely(features))
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
                    [geometries[idx] for idx in indexes],
                    grid_size=xy_tolerance)
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
