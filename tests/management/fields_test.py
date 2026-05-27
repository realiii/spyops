# -*- coding: utf-8 -*-
"""
Tests for Fields
"""


from datetime import datetime, timezone

from fudgeo import Field, Table
from fudgeo.enumeration import FieldType
from pytest import mark, approx

from spyops.management import (
    add_field, add_gps_metadata_fields,
    calculate_end_time, calculate_field, delete_field, alter_field,
    field_statistics_to_table, standardize_field)
from spyops.shared.enumeration import (
    FieldProperty, StandardizationMethod, StatisticOutputOption)
from spyops.shared.field import GNSS_COMMON_FIELDS

pytestmark = [mark.management, mark.field]


def test_delete_field(world_tables, mem_gpkg):
    """
    Test delete field
    """
    name = 'admin'
    table = world_tables[name].copy(
        name=name, geopackage=mem_gpkg, where_clause='ISO_CC = "BR"')
    assert len(table.fields) == 16
    delete_field(table, 'ISO_CC')
    assert len(table.fields) == 15
    delete_field(table, fields='NAME')
    assert len(table.fields) == 14
    delete_field(table, fields=['disputed', 'notes'])
    assert len(table.fields) == 12
# End test_delete_field function


def test_add_fields(world_tables, mem_gpkg):
    """
    Test add_field
    """
    name = 'admin'
    table = world_tables[name].copy(
        name=name, geopackage=mem_gpkg, where_clause='ISO_CC = "BR"')
    assert len(table.fields) == 16
    add_field(table)
    assert len(table.fields) == 16
    add_field(table, elements=table)
    assert len(table.fields) == 16
    add_field(table, elements=world_tables['cities'])
    assert len(table.fields) == 27
    add_field(table, fields=Field('pop_est', data_type='REAL'))
    assert len(table.fields) == 28
    add_field(table, fields=[Field('pop_est', data_type='REAL'),
                             Field('pop_density', data_type='REAL')])
    assert len(table.fields) == 29
    add_field(table, elements=[world_tables['cities'],
                               world_tables['disputed_boundaries']])
    assert len(table.fields) == 30
# End test_add_fields function


def test_calculate_field(world_tables, mem_gpkg):
    """
    Test calculate_field
    """
    name = 'admin'
    table = world_tables[name].copy(
        name=name, geopackage=mem_gpkg, where_clause='ISO_CC = "BR"')
    calculate_field(table, 'ISO_CC', expression='ISO_CC || ISO_CC')
    where_clause = 'ISO_CC = "BRBR"'
    cursor = table.select(where_clause=where_clause)
    assert len(cursor.fetchall()) == 62
    calculate_field(table, 'ISO_CC', expression='NAME', where_clause=where_clause)
# End test_calculate_field function


class TestAlterField:
    """
    Tester alter field
    """
    @staticmethod
    def _get_field(table, field_name) -> Field:
        """
        Get Field
        """
        fields = {f.name: f for f in table.fields}
        return fields[field_name]
    # End _get_field method

    @staticmethod
    def _copy_table(world_tables, mem_gpkg) -> tuple[str, Table]:
        """
        Copy Table
        """
        name = 'admin'
        field_name = 'ISO_CC'
        table = world_tables[name].copy(
            name=name, geopackage=mem_gpkg, where_clause=f'{field_name} = "BR"')
        return field_name, table
    # End _copy_table method

    def test_name(self, world_tables, mem_gpkg):
        """
        Test alter field name
        """
        field_name, table = self._copy_table(world_tables, mem_gpkg)
        new_name = 'ISO_COUNTRY_CODE'
        assert field_name in table.field_names
        assert new_name not in table.field_names
        alter_field(table, field=field_name, field_property=FieldProperty.NAME,
                    value=new_name)
        assert field_name not in table.field_names
        assert new_name in table.field_names
    # End test_name method

    def test_alias(self, world_tables, mem_gpkg):
        """
        Test alter field alias
        """
        field_name, table = self._copy_table(world_tables, mem_gpkg)
        field = self._get_field(table, field_name)
        assert field.alias is None
        assert field.comment is None

        alias = 'ISO Country Code'
        alter_field(table, field=field_name,
                    field_property=FieldProperty.ALIAS, value=alias)

        field = self._get_field(table, field_name)
        assert field.alias == alias
        assert field.comment is None

        alter_field(table, field=field_name,
                    field_property=FieldProperty.ALIAS, value=None)

        field = self._get_field(table, field_name)
        assert field.alias is None
        assert field.comment is None
    # End test_alias method

    def test_comment(self, world_tables, mem_gpkg):
        """
        Test alter field comment
        """
        field_name, table = self._copy_table(world_tables, mem_gpkg)
        field = self._get_field(table, field_name)
        assert field.alias is None
        assert field.comment is None

        comment = 'ISO Country Code'
        alter_field(table, field=field_name,
                    field_property=FieldProperty.COMMENT, value=comment)

        field = self._get_field(table, field_name)
        assert field.alias is None
        assert field.comment == comment

        alter_field(table, field=field_name,
                    field_property=FieldProperty.COMMENT, value=None)

        field = self._get_field(table, field_name)
        assert field.alias is None
        assert field.comment is None
    # End test_comment method
# End TestAlterField class


class TestAddGPSMetadataFields:
    """
    Test Add GPS Metadata Fields
    """
    def test_point_and_line(self, buffering, mem_gpkg):
        """
        Test point and line
        """
        names = 'airports_p', 'roads_l'
        for name in names:
            source = buffering[name].copy(name=name, geopackage=mem_gpkg)
            add_gps_metadata_fields(source)
    # End test_point_and_line method

    def test_existing_fields(self, buffering, mem_gpkg):
        """
        Test point and line, existing field
        """
        names = 'airports_p', 'roads_l'
        for name in names:
            source = buffering[name].copy(name=name, geopackage=mem_gpkg)
            source.add_fields(GNSS_COMMON_FIELDS)
            add_gps_metadata_fields(source)
    # End test_existing_fields method
# End TestAddGPSMetadataFields class


class TestCalculateEndTime:
    """
    Test Calculate End Time
    """
    def test_sans_sort(self, ntdb_zm_small, mem_gpkg):
        """
        Test sans sort
        """
        source = ntdb_zm_small['hydro_a'].copy(
            name='hydro_a', geopackage=mem_gpkg, where_clause='fid <= 50')
        name = 'later'
        source.add_fields([Field(name, data_type=FieldType.text)])
        calculate_end_time(source, start_field='valdate', end_field=name)
        cursor = source.select(name, include_geometry=False)
        values = [v for v, in cursor.fetchall()]
        assert values == [
            '1977', '1977', '1977', '1977', '1977', '1977', '1972', '1977',
            '1977', '1977', '1977', '1977', '1977', '1977', '1977', '1977',
            '1977', '1977', '1977', '1977', '1977', '1977', '1977', '1977',
            '1977', '1977', '1977', '1977', '1977', '1977', '1977', '1977',
            '1977', '1977', '1977', '1977', '1977', '1977', '1977', '1977',
            '1977', '1977', '1977', '1977', '1977', '1977', '1977', '1977',
            '1977', None]
    # End test_sans_sort method

    def test_with_sort(self, ntdb_zm_small, mem_gpkg):
        """
        Test with sort
        """
        source = ntdb_zm_small['hydro_a'].copy(
            name='hydro_a', geopackage=mem_gpkg, where_clause='fid <= 50')
        name = 'later_feature_id'
        source.add_fields([Field(name, data_type=FieldType.integer)])
        calculate_end_time(source, start_field='code', end_field=name,
                           sort_fields=['code', 'valdate'])
        cursor = source.select(name, include_geometry=False)
        values = [v for v, in cursor.fetchall()]
        assert values == [
            1480052, 1480052, 1480272, 1480052, 1480052, 1480052, 1480052,
            1480272, 1480052, 1480272, 1480052, 1480052, 1480052, 1480052,
            1480052, 1480052, 1480052, 1480052, 1480272, 1480052, 1480052,
            1480052, 1480052, 1480052, 1480052, 1480052, 1480052, 1480052,
            1480052, 1480052, 1480272, 1480052, 1480052, 1480052, 1480052,
            1480052, 1480052, 1480052, 1480052, 1480052, 1480052, 1480052,
            1480052, 1480052, 1480052, 1480272, None, 1480052, 1480062, 1480192]
    # End test_with_sort method
# End TestCalculateEndTime class


class TestFieldStatisticsToTable:
    """
    Test Field Statistics to Table
    """
    def test_numeric_sans_group(self, inputs, mem_gpkg):
        """
        Test numeric sans group
        """
        source = inputs['cl_run_messages']
        target = Table(geopackage=mem_gpkg, name='stats')
        fields = source.fields[1:]
        tbl = field_statistics_to_table(
            source, target, fields=fields, where_clause="""RECORD_ID > 10""")
        assert len(tbl) == 12
        assert len(tbl.field_names) == 24
        with tbl.geopackage.connection as cin:
            name = tbl.escaped_name
            cursor = cin.execute(f'SELECT FIELD_NAME FROM {name}')
            assert [n for n, in cursor.fetchall()] == [
                'SESSION_ID', 'RECORD_ID', 'SEGMENT_ID', 'DISTANCE', 'SPEED',
                'GPS_ACCURACY', 'ENHANCED_ALTITUDE', 'ALTITUDE', 'GRADE',
                'CADENCE', 'ENHANCED_SPEED', 'EMPTY']
            cursor = cin.execute(f'SELECT COUNT_NULL FROM {name}')
            assert [n for n, in cursor.fetchall()] == [
                0, 0, 0, 0, 0, 10, 10, 10, 5687, 4, 37, 5687]
            cursor = cin.execute(f'SELECT COUNT_NON_NULL FROM {name}')
            assert [n for n, in cursor.fetchall()] == [
                5687, 5687, 5687, 5687, 5687, 5677, 5677, 5677,
                0, 5683, 5650, 0]
            cursor = cin.execute(f'SELECT ROUND(MEAN, 1) FROM {name}')
            assert [n for n, in cursor.fetchall()] == [
                1.4, 1533.1, 1.6, 5517.4, 3.6, 1.0, 243.6, 243.6,
                None, 81.2, 3.6, None]
            cursor = cin.execute(f'SELECT ROUND(MODE, 1) FROM {name}')
            assert [n for n, in cursor.fetchall()] == [
                1.0, 11.0, 1.0, 9069.1, 0.0, 1.0, 248.6, 248.6,
                None, 82.0, 3.7, None]
    # End test_numeric_sans_group method

    def test_numeric_with_group(self, inputs, mem_gpkg):
        """
        Test numeric with group
        """
        source = inputs['cl_run_messages']
        target = Table(geopackage=mem_gpkg, name='stats')
        fields = source.fields[1:]
        tbl = field_statistics_to_table(
            source, target, fields=fields, group_fields='SESSION_ID',
            where_clause="""RECORD_ID > 10""")
        assert len(tbl) == 24
        assert len(tbl.field_names) == 25
        with tbl.geopackage.connection as cin:
            name = tbl.escaped_name
            cursor = cin.execute(f'SELECT SESSION_ID FROM {name}')
            assert [n for n, in cursor.fetchall()] == [
                1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2]
            cursor = cin.execute(f'SELECT FIELD_NAME FROM {name}')
            assert [n for n, in cursor.fetchall()] == [
                'SESSION_ID', 'SESSION_ID', 'RECORD_ID', 'RECORD_ID',
                'SEGMENT_ID', 'SEGMENT_ID', 'DISTANCE', 'DISTANCE', 'SPEED',
                'SPEED', 'GPS_ACCURACY', 'GPS_ACCURACY', 'ENHANCED_ALTITUDE',
                'ENHANCED_ALTITUDE', 'ALTITUDE', 'ALTITUDE', 'GRADE', 'GRADE',
                'CADENCE', 'CADENCE', 'ENHANCED_SPEED', 'ENHANCED_SPEED',
                'EMPTY', 'EMPTY']
            cursor = cin.execute(f'SELECT COUNT_NULL FROM {name}')
            assert [n for n, in cursor.fetchall()] == [
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 6, 4, 6, 4, 6, 4,
                3601, 2086, 1, 3, 23, 14, 3601, 2086]
            cursor = cin.execute(f'SELECT COUNT_NON_NULL FROM {name}')
            assert [n for n, in cursor.fetchall()] == [
                3601, 2086, 3601, 2086, 3601, 2086, 3601, 2086, 3601, 2086,
                3595, 2082, 3595, 2082, 3595, 2082, 0, 0, 3600, 2083, 3578,
                2072, 0, 0]
            cursor = cin.execute(f'SELECT ROUND(MEAN, 1) FROM {name}')
            assert [n for n, in cursor.fetchall()] == [
                1.0, 2.0, 1811.0, 1053.5, 1.6, 1.6, 6622.9, 3608.9, 3.7, 3.5,
                1.0, 1.0, 240.2, 249.4, 240.2, 249.4, None, None, 81.8, 80.3,
                3.7, 3.5, None, None]
            cursor = cin.execute(f'SELECT ROUND(MODE, 1) FROM {name}')
            assert [n for n, in cursor.fetchall()] == [
                1.0, 2.0, 11.0, 11.0, 1.0, 1.0, 9069.1, 3636.5, 0.0, 0.0, 1.0,
                1.0, 246.0, 248.6, 246.0, 248.6, None, None, 82.0, 82.0, 3.7,
                3.7, None, None]
    # End test_numeric_with_group method

    def test_text_sans_group(self, inputs, mem_gpkg):
        """
        Test text sans group
        """
        source = inputs['cl_run_messages']
        target = Table(geopackage=mem_gpkg, name='stats')
        fields = source.fields[1:]
        tbl = field_statistics_to_table(
            source, target, fields=fields,
            output_type_option=StatisticOutputOption.TEXT,
            where_clause="""RECORD_ID > 10""")
        assert len(tbl) == 1
        assert len(tbl.field_names) == 12
        with tbl.geopackage.connection as cin:
            name = tbl.escaped_name
            cursor = cin.execute(f'SELECT FIELD_NAME FROM {name}')
            assert [n for n, in cursor.fetchall()] == ['SIMPLE']
            cursor = cin.execute(f'SELECT COUNT_NULL FROM {name}')
            assert [n for n, in cursor.fetchall()] == [0]
            cursor = cin.execute(f'SELECT COUNT_NON_NULL FROM {name}')
            assert [n for n, in cursor.fetchall()] == [5687]
            cursor = cin.execute(f'SELECT MINIMUM FROM {name}')
            assert [n for n, in cursor.fetchall()] == ['0']
            cursor = cin.execute(f'SELECT MODE FROM {name}')
            assert [n for n, in cursor.fetchall()] == ['A']
    # End test_text_sans_group method

    def test_text_with_group(self, inputs, mem_gpkg):
        """
        Test text with group
        """
        source = inputs['cl_run_messages']
        target = Table(geopackage=mem_gpkg, name='stats')
        fields = source.fields[1:]
        tbl = field_statistics_to_table(
            source, target, fields=fields,
            output_type_option=StatisticOutputOption.TEXT,
            group_fields='SESSION_ID',
            where_clause="""RECORD_ID > 10""")
        assert len(tbl) == 2
        assert len(tbl.field_names) == 13
        with tbl.geopackage.connection as cin:
            name = tbl.escaped_name
            cursor = cin.execute(f'SELECT SESSION_ID FROM {name}')
            assert [n for n, in cursor.fetchall()] == [1, 2]
            cursor = cin.execute(f'SELECT FIELD_NAME FROM {name}')
            assert [n for n, in cursor.fetchall()] == ['SIMPLE', 'SIMPLE']
            cursor = cin.execute(f'SELECT COUNT_NULL FROM {name}')
            assert [n for n, in cursor.fetchall()] == [0, 0]
            cursor = cin.execute(f'SELECT COUNT_NON_NULL FROM {name}')
            assert [n for n, in cursor.fetchall()] == [3601, 2086]
            cursor = cin.execute(f'SELECT MINIMUM FROM {name}')
            assert [n for n, in cursor.fetchall()] == ['0', '0']
            cursor = cin.execute(f'SELECT MODE FROM {name}')
            assert [n for n, in cursor.fetchall()] == ['A', 'A']
    # End test_text_with_group method

    def test_date_sans_group(self, inputs, mem_gpkg):
        """
        Test date sans group
        """
        source = inputs['cl_run_messages']
        target = Table(geopackage=mem_gpkg, name='stats')
        fields = source.fields[1:]
        tbl = field_statistics_to_table(
            source, target, fields=fields,
            output_type_option=StatisticOutputOption.DATE,
            where_clause="""RECORD_ID > 10""")
        assert len(tbl) == 1
        assert len(tbl.field_names) == 17
        with tbl.geopackage.connection as cin:
            name = tbl.escaped_name
            cursor = cin.execute(f'SELECT FIELD_NAME FROM {name}')
            assert [n for n, in cursor.fetchall()] == ['RECORD_DATE']
            cursor = cin.execute(f'SELECT COUNT_NULL FROM {name}')
            assert [n for n, in cursor.fetchall()] == [0]
            cursor = cin.execute(f'SELECT COUNT_NON_NULL FROM {name}')
            assert [n for n, in cursor.fetchall()] == [5687]
            cursor = cin.execute(f'SELECT MINIMUM FROM {name}')
            assert [n for n, in cursor.fetchall()] == [datetime(2026, 5, 7, 17, 19, 7, tzinfo=timezone.utc)]
            cursor = cin.execute(f'SELECT MODE FROM {name}')
            assert [n for n, in cursor.fetchall()] == [datetime(2026, 5, 8, 15, 15, 36, tzinfo=timezone.utc)]
    # End test_date_sans_group method

    def test_date_with_group(self, inputs, mem_gpkg):
        """
        Test date with group
        """
        source = inputs['cl_run_messages']
        target = Table(geopackage=mem_gpkg, name='stats')
        fields = source.fields[1:]
        tbl = field_statistics_to_table(
            source, target, fields=fields,
            output_type_option=StatisticOutputOption.DATE,
            group_fields='SESSION_ID',
            where_clause="""RECORD_ID > 10""")
        assert len(tbl) == 2
        assert len(tbl.field_names) == 18
        with tbl.geopackage.connection as cin:
            name = tbl.escaped_name
            cursor = cin.execute(f'SELECT SESSION_ID FROM {name}')
            assert [n for n, in cursor.fetchall()] == [1, 2]
            cursor = cin.execute(f'SELECT FIELD_NAME FROM {name}')
            assert [n for n, in cursor.fetchall()] == ['RECORD_DATE', 'RECORD_DATE']
            cursor = cin.execute(f'SELECT COUNT_NULL FROM {name}')
            assert [n for n, in cursor.fetchall()] == [0, 0]
            cursor = cin.execute(f'SELECT COUNT_NON_NULL FROM {name}')
            assert [n for n, in cursor.fetchall()] == [3601, 2086]
            cursor = cin.execute(f'SELECT MINIMUM FROM {name}')
            assert [n for n, in cursor.fetchall()] == [
                datetime(2026, 5, 8, 15, 15, 36, tzinfo=timezone.utc),
                datetime(2026, 5, 7, 17, 19, 7, tzinfo=timezone.utc)]
            cursor = cin.execute(f'SELECT MODE FROM {name}')
            assert [n for n, in cursor.fetchall()] == [
                datetime(2026, 5, 8, 15, 15, 36, tzinfo=timezone.utc),
                datetime(2026, 5, 7, 17, 19, 7, tzinfo=timezone.utc)]
    # End test_date_with_group method
# End TestFieldStatisticsToTable class


class TestStandardizeField:
    """
    Test Standardize Field
    """
    @mark.parametrize('method, min_, max_', [
        (StandardizationMethod.Z_SCORE, -1.2091, 4.1793),
        (StandardizationMethod.MIN_MAX, 0, 50),
        (StandardizationMethod.ABSOLUTE_MAX, 0, 1),
        (StandardizationMethod.ROBUST, -0.7611, 3.4305),
    ])
    def test_method(self, inputs, mem_gpkg, method, min_, max_):
        """
        Test method
        """
        source = inputs['river_p'].copy(name='copy', geopackage=mem_gpkg)
        output_field = Field('distance_standard', data_type=FieldType.real)
        source.add_fields(output_field)
        kwargs = dict(source=source, standardization_method=method,
                      field=Field('distance', data_type=FieldType.real),
                      output_field=output_field, where_clause="""distance > 0""")
        if method == StandardizationMethod.MIN_MAX:
            kwargs['min_value'] = 0
            kwargs['max_value'] = 50
        standardize_field(**kwargs)
        with source.geopackage.connection as cin:
            name = source.escaped_name
            field_name = output_field.escaped_name
            cursor = cin.execute(f"""
                SELECT MIN({field_name}), MAX({field_name}) 
                FROM {name}
            """)
            results = cursor.fetchone()
            assert approx(results, abs=0.001) == (min_, max_)
    # End test method
# End TestStandardizeField class


if __name__ == '__main__':  # pragma: no cover
    pass
