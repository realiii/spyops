# -*- coding: utf-8 -*-
"""
Tests for Analysis utilities
"""


from pytest import mark

from spyops.analysis.util import _add_geometry_attribute_fields
from spyops.crs.enumeration import AreaUnit, LengthUnit
from spyops.shared.keywords import NAME_ATTR


pytestmark = [mark.utility, mark.analysis]


class TestAddGeometryAttributeFields:
    """
    Test Add Geometry Attribute Fields
    """
    @mark.parametrize('fc_name, expected', [
        ('hydro_a', (None, 'LENGTH', 'AREA')),
        ('structures_6654_zm_ma', (None, 'LENGTH', 'AREA')),
        ('transmission_l', (None, 'LENGTH', None)),
        ('transmission_6654_z_ml', (None, 'LENGTH', None)),
        ('toponymy_p', ('POINT_COUNT', None, None)),
        ('toponymy_zm_mp', ('POINT_COUNT', None, None)),
    ])
    def test_geometry_types(self, ntdb_zm_small, mem_gpkg, fc_name, expected):
        """
        Test geometry types
        """
        fc = ntdb_zm_small[fc_name].copy(name=fc_name, geopackage=mem_gpkg)
        fields = _add_geometry_attribute_fields(
            fc, length_unit=LengthUnit.METERS,
            area_unit=AreaUnit.SQUARE_METERS)
        names = [getattr(f, NAME_ATTR, f) for f in fields]
        assert names == list(expected)
    # End test_geometry_types method

    @mark.parametrize('fc_name, expected', [
        ('hydro_a', (None, 'LENGTH_1', 'AREA_1')),
        ('structures_6654_zm_ma', (None, 'LENGTH_1', 'AREA_1')),
        ('transmission_l', (None, 'LENGTH_1', None)),
        ('transmission_6654_z_ml', (None, 'LENGTH_1', None)),
        ('toponymy_p', ('POINT_COUNT_1', None, None)),
        ('toponymy_zm_mp', ('POINT_COUNT_1', None, None)),
    ])
    def test_geometry_types_existing(self, ntdb_zm_small, mem_gpkg, fc_name, expected):
        """
        Test geometry types where the fields already exist
        """
        fc = ntdb_zm_small[fc_name].copy(name=fc_name, geopackage=mem_gpkg)
        _add_geometry_attribute_fields(
            fc, length_unit=LengthUnit.METERS,
            area_unit=AreaUnit.SQUARE_METERS)
        fields = _add_geometry_attribute_fields(
            fc, length_unit=LengthUnit.METERS,
            area_unit=AreaUnit.SQUARE_METERS)
        names = [getattr(f, NAME_ATTR, f) for f in fields]
        assert names == list(expected)
    # End test_geometry_types_existing method
# End TestAddGeometryAttributeFields class


if __name__ == '__main__':  # pragma: no cover
    pass
