# -*- coding: utf-8 -*-
"""
Tests for Indexes
"""


from sqlite3 import IntegrityError

from fudgeo.enumeration import ShapeType
from pytest import mark, raises

from spyops.management import (
    add_spatial_index, remove_attribute_index,
    remove_spatial_index, add_attribute_index)


pytestmark = [mark.management, mark.indexes]


def test_add_spatial_index(mem_gpkg):
    """
    Test add spatial index
    """
    srs = mem_gpkg.spatial_references[4326]
    source = mem_gpkg.create_feature_class(
        'test_fc', shape_type=ShapeType.polygon, srs=srs,
        spatial_index=False)
    assert not source.has_spatial_index
    result = add_spatial_index(source)
    assert result is source
    assert source.has_spatial_index
# End test_add_spatial_index function


def test_remove_spatial_index(mem_gpkg):
    """
    Test add spatial index
    """
    srs = mem_gpkg.spatial_references[4326]
    source = mem_gpkg.create_feature_class(
        'test_fc', shape_type=ShapeType.polygon, srs=srs,
        spatial_index=True)
    assert source.has_spatial_index
    result = remove_spatial_index(source)
    assert result is source
    assert not source.has_spatial_index
# End test_remove_spatial_index function


@mark.parametrize('is_ascending', [
    True, False
])
@mark.parametrize('is_unique', [
    True, False
])
def test_add_attribute_index(world_tables, mem_gpkg, is_ascending, is_unique):
    """
    Test add_attribute_index
    """
    name = 'admin'
    table = world_tables[name].copy(
        name=name, geopackage=mem_gpkg, where_clause='ISO_CC = "BR"')
    assert len(table) == 62
    index_name = 'test_index'
    field_names = ['NAME', 'ISO_CC']
    if is_unique:
        with raises(IntegrityError):
            add_attribute_index(
                table, index_name, index_fields=field_names,
                is_ascending=is_ascending, is_unique=is_unique)
    else:
        result = add_attribute_index(
            table, index_name, index_fields=field_names,
            is_ascending=is_ascending, is_unique=is_unique)
        assert result is table
        assert table._check_index_exists(index_name)
# End test_add_attribute_index function


def test_remove_attribute_index(world_tables, mem_gpkg):
    """
    Test remove_attribute_index
    """
    name = 'admin'
    table = world_tables[name].copy(
        name=name, geopackage=mem_gpkg, where_clause='ISO_CC = "BR"')
    assert len(table) == 62
    index_name = 'test_index'
    field_names = ['NAME', 'ISO_CC']
    assert not table._check_index_exists(index_name)
    add_attribute_index(table, index_name, index_fields=field_names)
    assert table._check_index_exists(index_name)
    remove_attribute_index(table, 'asdf')
    remove_attribute_index(table, index_name)
    assert not table._check_index_exists(index_name)
# End remove_attribute_index function


if __name__ == '__main__':  # pragma: no cover
    pass
