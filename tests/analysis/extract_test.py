# -*- coding: utf-8 -*-
"""
Test Extraction
"""


from fudgeo import FeatureClass, Table
from pytest import mark, raises

from geomio.analysis.extract import select, table_select
from geomio.shared.exceptions import OperationsError


pytestmark = [mark.extract]


@mark.parametrize('table_name, where_clause, count', [
    ('admin', None, 5824),
    ('admin', '', 5824),
    ('admin', 'ISO_CC = "BR"', 62),
    ('disputed_boundaries', None, 561),
    ('disputed_boundaries', '', 561),
    ('disputed_boundaries', 'Description = "Disputed Boundary"', 364),
    ('cities', None, 2540),
    ('cities', '', 2540),
    ('cities', 'POP IS NULL', 1377),
    ('cities', 'POP < 0', 0),
])
def test_table_select(world_tables, fresh_gpkg, table_name, where_clause, count):
    """
    Test table_select
    """
    source = world_tables.tables[table_name]
    target = Table(geopackage=fresh_gpkg, name=table_name)
    result = table_select(source=source, target=target, where_clause=where_clause)
    assert result.count == count
# End test_table_select function


@mark.parametrize('table_name, where_clause', [
    ('admin', 'ISO = "BR"'),
    ('disputed_boundaries', 'Description = "Disputed Boundary'),
    ('cities', 'POP ISNULL()'),
    ('cities', 'POP <<>> 0'),
])
def test_table_select_bad_sql(world_tables, fresh_gpkg, table_name, where_clause):
    """
    Test table_select bad SQL
    """
    source = world_tables.tables[table_name]
    target = Table(geopackage=fresh_gpkg, name=table_name)
    with raises(OperationsError):
        table_select(source=source, target=target, where_clause=where_clause)
# End test_table_select_bad_sql function


@mark.parametrize('fc_name, where_clause, count', [
    ('lakes_a', None, 39),
    ('lakes_a', '', 39),
    ('lakes_a', 'SQKM > 5000', 28),
    ('disputed_boundaries_l', None, 561),
    ('disputed_boundaries_l', '', 561),
    ('disputed_boundaries_l', 'Description = "Disputed Boundary"', 364),
    ('cities_p', None, 2540),
    ('cities_p', '', 2540),
    ('cities_p', 'POP IS NULL', 1377),
    ('cities_p', 'POP < 0', 0),
])
def test_select(world_features, fresh_gpkg, fc_name, where_clause, count):
    """
    Test select
    """
    source = world_features.feature_classes[fc_name]
    target = FeatureClass(geopackage=fresh_gpkg, name=fc_name)
    result = select(source=source, target=target, where_clause=where_clause)
    assert result.count == count
# End test_select function


@mark.parametrize('fc_name, where_clause', [
    ('admin_a', 'ISO = "BR"'),
    ('disputed_boundaries_l', 'Description = "Disputed Boundary'),
    ('cities_p', 'POP ISNULL()'),
    ('cities_p', 'POP <<>> 0'),
])
def test_select_bad_sql(world_features, fresh_gpkg, fc_name, where_clause):
    """
    Test select bad SQL
    """
    source = world_features.feature_classes[fc_name]
    target = FeatureClass(geopackage=fresh_gpkg, name=fc_name)
    with raises(OperationsError):
        select(source=source, target=target, where_clause=where_clause)
# End test_select_bad_sql function


if __name__ == '__main__':  # pragma: no cover
    pass
