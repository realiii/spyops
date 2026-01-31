# -*- coding: utf-8 -*-
"""
Records Helper Functions
"""


from math import nan
from typing import Callable, TYPE_CHECKING, Type

from fudgeo.constant import FETCH_SIZE
from fudgeo.context import ExecuteMany
from fudgeo.geometry import PointM, PointZM
from fudgeo.geometry.point import MultiPointM, MultiPointZM
from shapely import GeometryCollection
from shapely.coordinates import get_coordinates
from shapely.io import from_wkb

from spyops.geometry.util import (
    filter_features, get_geoms, get_geoms_iter, to_shapely)
from spyops.geometry.wa import USE_WORKAROUNDS, set_precision
from spyops.shared.constant import GEOMS_ATTR, INCLUDE_M, INCLUDE_Z, SRS_ID_WKB
from spyops.shared.hint import XY_TOL


if TYPE_CHECKING:  # pragma: no cover
    from sqlite3 import Cursor
    from fudgeo.geometry.base import AbstractGeometry
    from spyops.geometry.config import GeometryConfig
    from spyops.shared.base import QueryConfig


def bulk_insert(cursor: 'Cursor', config: 'GeometryConfig',
                executor: 'ExecuteMany', transformer: Callable | None,
                insert_sql: str) -> None:
    """
    Bulk Insert
    """
    records = []
    while features := cursor.fetchmany(FETCH_SIZE):
        if not (features := filter_features(features)):
            continue
        insert_many(config, executor=executor, transformer=transformer,
                    insert_sql=insert_sql, features=features, records=records)
# End bulk_insert function


def insert_many(config: 'GeometryConfig', executor: 'ExecuteMany',
                transformer: Callable | None, insert_sql: str,
                features: list[tuple], records: list[tuple]) -> None:
    """
    Insert Many
    """
    geometries, validity = to_shapely(features, transformer=transformer)
    results = [(g, attrs) for g, (_, *attrs), valid in
               zip(geometries, features, validity) if valid]
    extend_records(results, records=records, config=config)
    executor(sql=insert_sql, data=records)
    records.clear()
# End insert_many function


def extend_records(results: list[tuple], records: list[tuple],
                   config: 'GeometryConfig') -> None:
    """
    Extend Records
    """
    srs_id = config.srs_id
    cls = config.geometry_cls
    combiner = config.combiner
    is_multi = config.is_multi
    types = _, multi_cls = config.filter_types
    refined = []
    for geom, attrs in results:
        if geom.is_empty:
            continue
        if isinstance(geom, GeometryCollection):
            geom = multi_cls([g for g in get_geoms(geom) if isinstance(g, types)])
        elif not isinstance(geom, types):
            continue
        geom = combiner(geom)
        if is_multi:
            if not hasattr(geom, GEOMS_ATTR):
                geom = multi_cls([geom])
            refined.append((geom, attrs))
        else:
            refined.extend([(g, attrs) for g in get_geoms_iter(geom)])
    if not refined:
        return
    if not config.caster:
        refined = _extend_measures(refined, cls)
        records.extend([(cls.from_wkb(geom.wkb, srs_id=srs_id), *attrs)
                        for geom, attrs in refined])
    else:
        geoms, attributes = zip(*refined)
        geoms = config.caster(geoms)
        records.extend([(geom, *attrs)
                        for geom, attrs in zip(geoms, attributes)])
# End extend_records function


def _extend_measures(refined: list, cls: Type['AbstractGeometry']) -> list:
    """
    Extend shapely PointZ / MultiPointZ with Measures (when needed)
    """
    if cls not in (PointM, PointZM, MultiPointM, MultiPointZM):
        return refined
    if not USE_WORKAROUNDS.dropped_nan_measures:
        return refined
    corrected = []
    if cls in (PointM, PointZM):
        kwargs = {INCLUDE_Z: cls is PointZM}
        for geom, attrs in refined:
            if not geom.has_m:
                values, = get_coordinates(geom, **kwargs)
                # noinspection PyUnresolvedReferences
                geom = from_wkb(cls.from_tuple(
                    (*values, nan), srs_id=SRS_ID_WKB).wkb)
            corrected.append((geom, attrs))
    else:
        kwargs = {INCLUDE_Z: cls is MultiPointZM, INCLUDE_M: True}
        for geom, attrs in refined:
            if not geom.has_m:
                coords = get_coordinates(geom, **kwargs)
                # noinspection PyArgumentList
                geom = from_wkb(cls(coords, srs_id=SRS_ID_WKB).wkb)
            corrected.append((geom, attrs))
    return corrected
# End _extend_measures function


def process_disjoint(query: 'QueryConfig', xy_tolerance: XY_TOL) -> None:
    """
    Process Disjoint Features
    """
    if not query.disjoint:
        return
    records = []
    insert_sql = query.insert
    with (query.target.geopackage.connection as cout,
          query.source.geopackage.connection as cin,
          ExecuteMany(connection=cout, table=query.target) as executor):
        cursor = cin.execute(query.disjoint)
        while features := cursor.fetchmany(FETCH_SIZE):
            geometries = to_shapely(features)
            if xy_tolerance is not None:
                geometries = set_precision(geometries, grid_size=xy_tolerance)
            results = [(geom, attrs) for geom, (_, *attrs) in
                       zip(geometries, features)]
            extend_records(results, records=records, config=query.config)
            executor(sql=insert_sql, data=records)
            records.clear()
# End process_disjoint function


if __name__ == '__main__':  # pragma: no cover
    pass
