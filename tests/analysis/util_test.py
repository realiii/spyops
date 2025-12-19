# -*- coding: utf-8 -*-
"""
Test Utility Functions
"""

from pytest import mark

from geomio.analysis.util import shared_select


pytestmark = [mark.extract]


@mark.parametrize('name, where_clause, count', [
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
def test_shared_select(world_tables, world_features, mem_gpkg, name, where_clause, count):
    """
    Test shared_select
    """
    source = world_tables[name] or world_features[name]
    target = source.__class__(geopackage=mem_gpkg, name=name)
    result = shared_select(source=source, target=target, where_clause=where_clause, overwrite=True)
    assert result.count == count
# End test_shared_select function


if __name__ == '__main__':  # pragma: no cover
    pass
