# -*- coding: utf-8 -*-
"""
Query Classes for management.statistics module
"""


from functools import cache, cached_property
from typing import Generator, TYPE_CHECKING

from fudgeo.constant import COMMA_SPACE, FETCH_SIZE
from numpy import array, isin

from spyops.environment import ANALYSIS_SETTINGS
from spyops.query.base import AbstractElementGroupQuery, BaseQuerySelect
from spyops.query.mixin import StatisticsMixin
from spyops.shared.constant import EMPTY
from spyops.shared.enumeration import GeometryAttribute
from spyops.shared.field import (
    FEAT_COUNT, FREQUENCY, ORIG_FID, add_key_fields, clone_field,
    get_geometry_column_name, make_field_names, make_unique_fields)
from spyops.shared.hint import ELEMENT, FIELDS, OPT_FIELD, STATS_FIELDS
from spyops.shared.stats import Frequency, Sum


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass, Table
    from numpy import ndarray


class BaseSummaryStatistics(StatisticsMixin, AbstractElementGroupQuery):
    """
    Base Summary Statistics
    """
    def __init__(self, element: ELEMENT, target: 'Table',
                 statistics: STATS_FIELDS, fields: FIELDS,
                 where_clause: str) -> None:
        """
        Initialize the BaseSummaryStatistics class
        """
        super().__init__(element, fields=fields)
        self._target: 'Table' = target
        self._statistics: STATS_FIELDS = statistics
        self._where_clause: str = where_clause
    # End init built-in

    @cache
    def _field_names_and_count(self, element: ELEMENT) \
            -> tuple[int, str, str]:
        """
        Field Names for Select and Insert + Derive Field Count
        """
        field_count = len(self._fields) + len(self.statistics)
        select_names = self._make_select_names(self._fields, self.statistics)
        insert_names = self._make_insert_names(self._fields)
        return field_count, insert_names, select_names
    # End _field_names_and_count method

    def _make_insert_names(self, fields: FIELDS) -> str:
        """
        Make Insert Names
        """
        insert_names = make_field_names(fields)
        stats_fields = self._get_unique_fields()[len(fields):]
        insert_stats = make_field_names(stats_fields)
        if insert_names:
            return self._concatenate(insert_names, insert_stats)
        return insert_stats
    # End _make_insert_names method

    def _make_select_names(self, fields: FIELDS, stats: STATS_FIELDS) -> str:
        """
        Make Select Names
        """
        select_names = make_field_names(fields)
        select_stats = COMMA_SPACE.join([s.aggregate for s in stats])
        if select_names:
            return self._concatenate(select_names, select_stats)
        return select_stats
    # End _make_select_names method

    @property
    def select(self) -> str:
        """
        Select
        """
        elm = self.source
        # noinspection argument-list
        *_, select_field_names = self._field_names_and_count(elm)
        where_clause = self._get_where_clause()
        if not self._group_names:
            return self._make_select(
                elm, field_names=select_field_names, where_clause=where_clause)
        return f"""
            SELECT {select_field_names}
            FROM {elm.escaped_name} 
            WHERE {where_clause}
            GROUP BY {self._group_names}
        """
    # End select property

    @property
    def insert(self) -> str:
        """
        Insert
        """
        # noinspection argument-list
        field_count, insert_names, _ = self._field_names_and_count(self.target)
        return self._make_insert(
            self.target.escaped_name, field_names=insert_names,
            field_count=field_count)
    # End insert property

    @property
    def target(self) -> 'Table':
        """
        Target
        """
        return self.target_empty
    # End target property

    @cached_property
    def target_empty(self) -> 'Table':
        """
        Target Empty
        """
        return self._target.geopackage.create_table(
            self._target.name, fields=self._get_unique_fields(),
            overwrite=ANALYSIS_SETTINGS.overwrite)
    # End target_empty property
# End BaseSummaryStatistics class


class QueryStatistics(BaseSummaryStatistics):
    """
    Query Statistics
    """
# End QueryStatistics class


class QueryFrequency(BaseSummaryStatistics):
    """
    Query Frequency
    """
    def __init__(self, element: ELEMENT, target: 'Table',
                 statistics: STATS_FIELDS, fields: FIELDS,
                 where_clause: str) -> None:
        """
        Initialize the QueryFrequency class
        """
        super().__init__(element, target=target, statistics=statistics,
                         fields=fields, where_clause=where_clause)
        self._statistics: STATS_FIELDS = [
            self._get_frequency_stat(fields), *statistics]
    # End init built-in

    @staticmethod
    def _get_frequency_stat(fields: FIELDS) -> Frequency:
        """
        Get Frequency Statistics with output name set
        """
        stat = Frequency()
        *_, frequency = add_key_fields([FREQUENCY], fields)
        stat.output_name = frequency.name
        return stat
    # End _get_frequency_stat method
# End QueryFrequency class


class QueryTabulateIntersection(BaseSummaryStatistics):
    """
    Query Tabulate Intersection
    """
    def __init__(self, source: 'FeatureClass', operator: 'FeatureClass',
                 intermediate: 'FeatureClass', target: 'Table',
                 group_fields: FIELDS, class_fields: FIELDS,
                 statistics: STATS_FIELDS, count_field: OPT_FIELD,
                 length_field: OPT_FIELD, area_field: OPT_FIELD) -> None:
        """
        Initialize the QueryTabulateIntersection class
        """
        intermediate_fields, target_fields = self._rebuild_fields(
            source, operator=operator, intermediate=intermediate,
            group_fields=group_fields, class_fields=class_fields)
        stats_output_fields = self._get_stats_output_fields(statistics)
        geom_fields, geom_stats = self._rebuild_geom_stats(
            (*target_fields, *stats_output_fields), count_field=count_field,
            length_field=length_field, area_field=area_field)
        super().__init__(intermediate, target=target, statistics=statistics,
                         fields=target_fields, where_clause=EMPTY)
        self._intermediate_fields: FIELDS = intermediate_fields
        self._stats_fields: FIELDS = stats_output_fields
        self._geom_fields: FIELDS = geom_fields
        self._geom_stats: STATS_FIELDS = geom_stats
    # End init built-in

    @staticmethod
    def _get_stats_output_fields(statistics: STATS_FIELDS) -> FIELDS:
        """
        Get Statistic Output Fields, Removing Repeated Stats
        """
        fields = []
        output_names = set()
        for stat in statistics:
            field = stat.output_field
            name = field.name.casefold()
            if name in output_names:
                continue
            fields.append(field)
            output_names.add(name)
        return fields
    # End _get_stats_output_fields method

    @staticmethod
    def _get_renamed_fields(source: 'FeatureClass', operator: 'FeatureClass',
                            intermediate: 'FeatureClass',
                            fields: FIELDS) -> FIELDS:
        """
        Get Fields from Intermediate in same order as input Fields, relying
        on indexing to translate from original name to potentially renamed name.
        """
        # NOTE get the attribute columns, ignore Primary Key and Geometry
        src_fields = source.fields[2:]
        int_fields = intermediate.fields[(len(operator.fields)):]
        return [int_fields[src_fields.index(f)] for f in fields]
    # End _get_renamed_fields method

    def _rebuild_fields(self, source: 'FeatureClass', operator: 'FeatureClass',
                        intermediate: 'FeatureClass', group_fields: FIELDS,
                        class_fields: FIELDS) -> tuple[FIELDS, FIELDS]:
        """
        Rebuild field names by translating class field names to renamed field
        names in the intermediate feature class.  Build up a list of the
        intermediate fields (present in the intermediate feature class) and
        the target fields (the prettiest names possible for target definition).
        """
        target_fields = []
        intermediate_fields = []
        renamed_fields = self._get_renamed_fields(
            source, operator=operator, intermediate=intermediate,
            fields=group_fields)
        class_names = {f.name.casefold() for f in class_fields}
        for group_field, renamed_field in zip(group_fields, renamed_fields):
            intermediate_fields.append(renamed_field)
            if group_field.name.casefold() not in class_names:
                target_fields.append(group_field)
            else:
                target_fields.append(renamed_field)
        target_fields.extend(class_fields)
        intermediate_fields.extend(class_fields)
        return intermediate_fields, target_fields
    # End _rebuild_fields method

    @staticmethod
    def _rebuild_geom_stats(fields: FIELDS, count_field: OPT_FIELD,
                            length_field: OPT_FIELD, area_field: OPT_FIELD) \
            -> tuple[FIELDS, STATS_FIELDS]:
        """
        Rebuild Geometry Statistics Fields in an attempt to build out the
        target table with the nicest field names possible.
        """
        geom_stats = []
        geom_fields = []
        sum_fields = count_field, length_field, area_field
        if not any(sum_fields):
            return geom_fields, geom_stats
        names = {f.name.casefold() for f in fields}
        attrs = (GeometryAttribute.POINT_COUNT, GeometryAttribute.LENGTH,
                 GeometryAttribute.AREA)
        for attr, field in zip(attrs, sum_fields):
            if not field:
                continue
            name = str(attr)
            if name not in names:
                geom_fields.append(clone_field(field, name.upper()))
            else:
                geom_fields.append(field)
            geom_stats.append(Sum(field))
        return geom_fields, geom_stats
    # End _rebuild_geom_stats method

    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields
        """
        fields = self._fields
        stat_fields = make_unique_fields(fields, self._stats_fields)
        geom_fields = make_unique_fields(
            (*fields, *stat_fields), self._geom_fields)
        return [*fields, *stat_fields, *geom_fields]
    # End _get_unique_fields method

    @cache
    def _field_names_and_count(self, element: ELEMENT) \
            -> tuple[int, str, str]:
        """
        Field Names for Select and Insert + Derive Field Count
        """
        stats = *self.statistics, *self._geom_stats
        field_count = len(self._fields) + len(stats)
        select_names = self._make_select_names(self._intermediate_fields, stats)
        insert_names = self._make_insert_names(self._fields)
        return field_count, insert_names, select_names
    # End _field_names_and_count method
# End QueryTabulateIntersection class


class QueryTabulateIntersectionSummarizeWithin(QueryTabulateIntersection):
    """
    Query Tabulate Intersection for Summarize Within
    """
    def __init__(self, source: 'FeatureClass', operator: 'FeatureClass',
                 intermediate: 'FeatureClass', target: 'Table',
                 group_fields: FIELDS, class_fields: FIELDS,
                 statistics: STATS_FIELDS, count_field: OPT_FIELD,
                 length_field: OPT_FIELD, area_field: OPT_FIELD) -> None:
        """
        Initialize the QueryTabulateIntersectionSummarizeWithin class
        """
        super().__init__(
            source, operator=operator, intermediate=intermediate,
            target=target, group_fields=group_fields, class_fields=class_fields,
            statistics=statistics, count_field=count_field,
            length_field=length_field, area_field=area_field)
    # End init built-in

    def _rebuild_fields(self, source: 'FeatureClass', operator: 'FeatureClass',
                        intermediate: 'FeatureClass', group_fields: FIELDS,
                        class_fields: FIELDS) -> tuple[FIELDS, FIELDS]:
        """
        Rebuild field names -- here we just pass through the group fields
        since the group field is really a reference to the source FID column.
        Done this way to avoid attempting to add two FID columns.  Final
        renaming handled in QuerySummarizeWithinFeatureClass.
        """
        fields = *group_fields, *class_fields
        return fields, fields
    # End _rebuild_fields method
# End QueryTabulateIntersectionSummarizeWithin class


class QuerySummarizeWithinFeatureClass(BaseQuerySelect):
    """
    Query Summarize Within -- Feature Class output
    """
    def __init__(self, source: 'FeatureClass', target: 'FeatureClass',
                 summary: 'Table', keep_all: bool) -> None:
        """
        Initialize the QuerySummarizeWithinFeatureClass class
        """
        super().__init__(source, target=target)
        self._summary: 'Table' = summary
        self._keep_all: bool = keep_all
    # End init built-in

    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields, need to use the summary table for the field names,
        ensure support for Null values when keep all is True, force the first
        field to be ORIG_FID.
        """
        key_fields = ORIG_FID, FEAT_COUNT
        # NOTE exclude primary key, original fid, and count of fid
        fields = add_key_fields(self._summary.fields[3:], key_fields)
        if not self._keep_all:
            return fields
        # NOTE original fid will always have a value
        for field in fields[1:]:
            field.is_nullable = True
        return fields
    # End _get_unique_fields method

    def build_features(self) -> Generator[list[tuple], None, None]:
        """
        Build Features
        """
        geometries, fids = self._get_source_data()
        if not len(geometries):
            return
        visited = set()
        # NOTE select all fields except primary key
        cursor = self._summary.select(self._summary.fields[1:])
        while records := cursor.fetchmany(FETCH_SIZE):
            orig_fids, *_ = zip(*records)
            visited.update(orig_fids)
            geoms = geometries[isin(orig_fids, fids)]
            yield [(g, *rec) for g, rec in zip(geoms, records)]
        if not self._keep_all:
            return
        if not (missing := set(fids) - visited):
            return
        missing = sorted(missing)
        geoms = geometries[isin(missing, fids)]
        empty = (None,) * (len(cursor.description) - 1)
        yield [(g, fid, *empty) for g, fid in zip(geoms, missing)]
    # End build_features method

    def _get_source_data(self) -> tuple['ndarray', 'ndarray']:
        """
        Get Source Data -- returning fudgeo geometry and FID integers, this
        will only be the features within the extent.
        """
        with self.source.geopackage.connection as cin:
            cursor = cin.execute(self.select_only_fid)
            features = cursor.fetchall()
        if not features:
            return array([]), array([])
        geometries, fids = zip(*features)
        return array(geometries, dtype=object), array(fids, dtype=int)
    # End _get_source_data method

    @property
    def insert(self) -> str:
        """
        Insert Query
        """
        elm = self.target
        fields = self._get_unique_fields()
        geom = get_geometry_column_name(elm)
        insert_field_names = make_field_names(fields)
        insert_field_names = self._concatenate(geom, insert_field_names)
        return self._make_insert(
            elm.escaped_name, field_names=insert_field_names,
            field_count=len(fields) + 1)
    # End insert property
# End QuerySummarizeWithinFeatureClass class


class QuerySummarizeWithinTable(BaseQuerySelect):
    """
    Query Summarize Within -- Table output
    """
    def __init__(self, summary: 'Table', target: 'Table') -> None:
        """
        Initialize the QuerySummarizeWithinTable class
        """
        # noinspection bad-argument-type
        super().__init__(summary, target=target)
    # End init built-in

    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields, rework the order of the fields place group by fields
        at the start then followed by statistics.
        """
        key_fields = ORIG_FID, FEAT_COUNT
        _, _, class_field, _, *fields = self.source.fields
        orig_fid, feat_count, class_field, *fields = add_key_fields(
            [class_field, *fields], key_fields)
        return orig_fid, class_field, feat_count, *fields
    # End _get_unique_fields method

    @property
    def select(self) -> str:
        """
        Select
        """
        elm = self.source
        _, *fields = elm.fields
        select_field_names = make_field_names(fields)
        where_clause = self._get_where_clause()
        return self._make_select(
            elm, field_names=select_field_names, where_clause=where_clause)
    # End select property

    @property
    def insert(self) -> str:
        """
        Insert Query
        """
        elm = self.target
        fields = self._get_unique_fields()
        insert_field_names = make_field_names(fields)
        return self._make_insert(
            elm.escaped_name, field_names=insert_field_names,
            field_count=len(fields))
    # End insert property
# End QuerySummarizeWithinTable class


if __name__ == '__main__':  # pragma: no cover
    pass
