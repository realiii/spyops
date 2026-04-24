# -*- coding: utf-8 -*-
"""
Tests for Fields
"""


from fudgeo import Field, Table
from pytest import mark

from spyops.management import (
    add_field, add_gps_metadata_fields,
    calculate_field, delete_field, alter_field)
from spyops.shared.enumeration import FieldProperty
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


if __name__ == '__main__':  # pragma: no cover
    pass
