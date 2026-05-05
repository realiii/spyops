# -*- coding: utf-8 -*-
"""
Tests for Geopackage Conversion Classes
"""


from pytest import mark

from spyops.environment import Setting
from spyops.environment.context import Swap
from spyops.query.conversion.geopackage import QueryTableToGeoPackage


pytestmark = [mark.conversion, mark.geopackage, mark.query]


class TestQueryTableToGeoPackage:
    """
    Test Query Table to GeoPackage
    """
    @mark.parametrize('overwrite, expected', [
        (True, 'hydro_zm_a'),
        (False, 'hydro_zm_a_1'),
    ])
    def test_make_target(self, ntdb_zm_small, overwrite, expected):
        """
        Test make target
        """
        source = ntdb_zm_small['hydro_zm_a']
        with Swap(Setting.OVERWRITE, overwrite):
            target = QueryTableToGeoPackage._make_target(source, ntdb_zm_small)
            assert target.name == expected
    # End test_make_target method
# End TestQueryTableToGeoPackage class


if __name__ == '__main__':  # pragma: no cover
    pass
