# -*- coding: utf-8 -*-
"""
Test for General Query classes
"""


from pytest import mark

from spyops.query.management.general import (
    QueryFindIdenticalFeatureClass,
    QueryFindIdenticalTable)
from spyops.shared.field import REASON

pytestmark = [mark.general, mark.query, mark.management]


class TestQueryFindIdenticalTable:
    """
    Test Query Find Identical Table
    """
    def test_select(self):
        """
        Test select
        """
        query = QueryFindIdenticalTable(None, None, [])
        assert not query.select
    # End test_select method

    def test_has_zm(self):
        """
        Test Has ZM
        """
        query = QueryFindIdenticalTable(None, None, [])
        assert query.has_zm == (False, False)
    # End test_has_zm method
# End TestQueryFindIdenticalTable class


class TestQueryFindIdenticalFeatureClass:
    """
    Test Query Find Identical Feature Class
    """
    def test_select(self, identical):
        """
        Test select
        """
        source = identical['point_p']
        query = QueryFindIdenticalFeatureClass(
            source, target=None, fields=[REASON], include_geometry=False,
            xy_tolerance=None, z_tolerance=None, m_tolerance=None)
        assert not query.select
        query = QueryFindIdenticalFeatureClass(
            source, target=None, fields=[REASON], include_geometry=True,
            xy_tolerance=None, z_tolerance=None, m_tolerance=None)
        assert query.select
    # End test_select method

    @mark.parametrize('fc_name, expected', [
        ('hydro_a', (False, False)),
        ('hydro_m_a', (False, True)),
        ('hydro_zm_a', (True, True)),
    ])
    def test_has_zm(self, ntdb_zm_small, fc_name, expected):
        """
        Test Has ZM
        """
        source = ntdb_zm_small[fc_name]
        query = QueryFindIdenticalFeatureClass(
            source, target=None, fields=[REASON], include_geometry=False,
            xy_tolerance=None, z_tolerance=None, m_tolerance=None)
        assert query.has_zm == expected
    # End test_has_zm method

    def test_grid_size(self, identical):
        """
        Test Grid Size
        """
        source = identical['point_p']
        query = QueryFindIdenticalFeatureClass(
            source, target=None, fields=[REASON], include_geometry=False,
            xy_tolerance=100, z_tolerance=None, m_tolerance=None)
        assert query.grid_size == 100
    # End test_grid_size method
# End TestQueryFindIdenticalFeatureClass class


if __name__ == '__main__':  # pragma: no cover
    pass
