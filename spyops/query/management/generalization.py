# -*- coding: utf-8 -*-
"""
Query Classes for management.generalization module
"""


from collections import Counter
from concurrent.futures.process import ProcessPoolExecutor, _MAX_WINDOWS_WORKERS
from functools import cache, cached_property, partial
# noinspection PyProtectedMember
from os import process_cpu_count
from statistics import median
from sys import platform
from typing import Generator, Self, TYPE_CHECKING

from fudgeo.constant import COMMA_SPACE, FETCH_SIZE
from fudgeo.enumeration import ShapeType
from numpy import array

from spyops.geometry.multi import build_dissolved
from spyops.geometry.util import filter_features, to_shapely
from spyops.query.base import AbstractSourceQuery, GroupQueryMixin
from spyops.shared.constant import DRID
from spyops.shared.database import (
    add_aggregates, remove_aggregates)
from spyops.shared.field import (
    get_geometry_column_name, make_field_names, make_unique_fields)
from spyops.shared.hint import ELEMENT, FIELDS, STATS_FIELDS, XY_TOL


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass
    from shapely.geometry.base import BaseMultipartGeometry
    from numpy import ndarray


class QueryDissolve(GroupQueryMixin, AbstractSourceQuery):
    """
    Queries for Dissolve
    """
    def __init__(self, source: 'FeatureClass', target: 'FeatureClass', *,
                 fields: FIELDS, statistics: STATS_FIELDS, as_multi_part: bool,
                 xy_tolerance: XY_TOL) -> None:
        """
        Initialize the QueryDissolve class
        """
        super().__init__(source, target=target, xy_tolerance=xy_tolerance)
        self._fields: FIELDS = fields
        self._statistics: STATS_FIELDS = statistics
        self._as_multi_part: bool = as_multi_part
        self._group_names: str = make_field_names(fields)
    # End init built-in

    def __enter__(self) -> Self:
        """
        Context Manager Enter
        """
        add_aggregates(self.source.geopackage.connection)
        return self
    # End enter built-in

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Context Manager Exit
        """
        remove_aggregates(self.source.geopackage.connection)
        return False
    # End exit built-in

    @cache
    def _field_names_and_count(self, element: ELEMENT) -> tuple[int, str, str]:
        """
        Field Names for Select and Insert + Derive Field Count
        """
        fields = self._fields
        stats = self.statistics
        field_count = len(fields) + len(stats) + 1

        select_names = insert_names = make_field_names(fields)
        select_names = self._concatenate(DRID, select_names)
        select_stats = COMMA_SPACE.join([s.aggregate for s in stats])
        select_names = self._concatenate(select_names, select_stats)

        stats_fields = self._get_unique_fields()[len(fields):]
        insert_stats = make_field_names(stats_fields)
        insert_names = self._concatenate(insert_names, insert_stats)
        geom = get_geometry_column_name(element)
        insert_names = self._concatenate(geom, insert_names)
        return field_count, insert_names, select_names
    # End _field_names_and_count method

    def _get_target_shape_type(self) -> str:
        """
        Get Target Shape Type based on Output Type Option and Source Shape Type
        """
        if (self._as_multi_part and self.source.is_multi_part) or (
                not self._as_multi_part and not self.source.is_multi_part):
            return self.source.shape_type
        lut = {ShapeType.polygon: ShapeType.multi_polygon,
               ShapeType.linestring: ShapeType.multi_linestring,
               ShapeType.point: ShapeType.multi_point,
               ShapeType.multi_point: ShapeType.point,
               ShapeType.multi_linestring: ShapeType.linestring,
               ShapeType.multi_polygon: ShapeType.polygon}
        return lut[self.source.shape_type]
    # End _get_target_shape_type method

    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields
        """
        stat_fields = [stat.output_field for stat in self.statistics]
        stat_fields = make_unique_fields(self._fields, stat_fields)
        return [*self._fields, *stat_fields]
    # End _get_unique_fields method

    @staticmethod
    def _get_worker_count() -> int:
        """
        Get Worker Count
        """
        count = process_cpu_count() or 1
        if platform == 'win32':
            count = min(count, _MAX_WINDOWS_WORKERS)
        return max(1, int(round(count * 0.75)))
    # End _get_worker_count method

    @staticmethod
    def _use_serial(ids: 'ndarray', shape_type: str, worker_count: int) -> bool:
        """
        Use Serial Processing
        """
        if ShapeType.point in shape_type or worker_count == 1:
            return True
        counter = Counter(ids)
        if len(counter) <= worker_count:
            return True
        # NOTE checking if there is much grouping
        return median(counter.values()) <= 2
    # End _use_serial method

    @property
    def select(self) -> str:
        """
        Selection Query
        """
        elm = self.source
        *_, select_field_names = self._field_names_and_count(elm)
        dr_select_names = make_field_names(self._fields)
        dr_select_stats = make_field_names([s.field for s in self.statistics])
        dr_select_names = self._concatenate(dr_select_names, dr_select_stats)
        # NOTE this extent not used, simply filling a required argument
        index_where = self._spatial_index_where(elm, extent=(0, 0, 0, 0))
        # noinspection PyUnresolvedReferences
        return f"""
            SELECT {select_field_names}
            FROM (SELECT dense_rank() OVER (
                    ORDER BY {self._group_names}) AS {DRID}, {dr_select_names} 
                  FROM {elm.escaped_name} {index_where})
            GROUP BY {DRID} 
        """
    # End select property

    @property
    def insert(self) -> str:
        """
        Insert Query
        """
        elm = self.target
        field_count, insert_field_names, _ = self._field_names_and_count(elm)
        return self._make_insert(
            elm.escaped_name, field_names=insert_field_names,
            field_count=field_count)
    # End insert property

    @property
    def select_geometry(self) -> str:
        """
        Select Geometry
        """
        elm = self.source
        geom = get_geometry_column_name(elm, include_geom_type=True)
        # NOTE this extent not used, simply filling a required argument
        index_where = self._spatial_index_where(elm, extent=(0, 0, 0, 0))
        return f"""
            SELECT * 
            FROM (SELECT {geom}, dense_rank() OVER (
                    ORDER BY {self._group_names}) AS {DRID}
                  FROM {elm.escaped_name} {index_where})
            WHERE {DRID} BETWEEN ? AND ?
        """
    # End select_geometry property

    def dissolved_geometries(self) -> Generator[
            dict[int, 'BaseMultipartGeometry'], None]:
        """
        Dissolved Geometries stored as a dictionary of Dense Range IDs
        and Multi-Part Geometries.  Page over the number of groups to
        avoid loading all geometries into memory at once.

        This method builds up a dictionary of geometries and yields it when it
        reaches (or exceeds) fetch size.  There is an expectation that when a
        geometry is stitched together with its aggregate row that the geometry
        will be popped from the dictionary.
        """
        dissolved = {}
        size = FETCH_SIZE // 5
        steps, remainder = divmod(self.group_count, size)
        steps += bool(remainder)
        sql = self.select_geometry
        shape_type = self.source.shape_type
        worker_count = self._get_worker_count()
        builder = partial(build_dissolved, shape_type=shape_type,
                          grid_size=self.grid_size)
        with self.source.geopackage.connection as cin:
            for step in range(steps):
                start = 1 + (step * size)
                end = (step + 1) * size
                cursor = cin.execute(sql, (start, end))
                features = filter_features(cursor.fetchall())
                features, geometries = to_shapely(
                    features, transformer=self.source_transformer)
                ids = array([i for _, i in features], dtype=int)
                unique_ids = set(ids)
                if self._use_serial(ids, shape_type=shape_type,
                                    worker_count=worker_count):
                    results = {i: builder(geometries[ids == i])
                               for i in unique_ids}
                else:
                    parts = [geometries[ids == i] for i in unique_ids]
                    with ProcessPoolExecutor(max_workers=worker_count) as ppe:
                        results = ppe.map(builder, parts)
                        results = {i: result for i, result in
                                   zip(unique_ids, results)}
                dissolved.update(results)
                if len(dissolved) >= FETCH_SIZE:
                    yield dissolved
        yield dissolved
    # End dissolved_geometries method

    @cached_property
    def statistics(self) -> STATS_FIELDS:
        """
        Statistics with repeated output names removed
        """
        keepers = []
        names = set()
        for stat in self._statistics:
            name = stat.output_name.casefold()
            if name in names:
                continue
            names.add(name)
            keepers.append(stat)
        return keepers
    # End statistics property

    @cached_property
    def group_count(self) -> int:
        """
        Group Count
        """
        elm = self.source
        with elm.geopackage.connection as cin:
            cursor = cin.execute(f"""
                SELECT COUNT(*) AS CNT 
                FROM (SELECT DISTINCT {self._group_names} 
                      FROM {elm.escaped_name})
            """)
            count, = cursor.fetchone()
        return count
    # End group_count property
# End QueryDissolve class


if __name__ == '__main__':  # pragma: no cover
    pass
