# -*- coding: utf-8 -*-
"""
Test for Proximity Query classes
"""
from fudgeo import Field
from fudgeo.enumeration import FieldType, ShapeType
from pytest import mark

from spyops.crs.unit import DecimalDegrees, Meters, Miles
from spyops.query.management.proximity import (
    QueryBufferDissolveAll, QueryBufferDissolveList)
from spyops.shared.enumeration import BufferTypeOption, EndOption, SideOption

pytestmark = [mark.proximity, mark.query, mark.analysis]


class TestQueryBufferDissolveList:
    """
    Test QueryBufferDissolveList
    """
    @mark.parametrize('distance, expected', [
        (Field('MIX_UNIT', data_type=FieldType.text), True),
        (Meters(5000), False),
        (Miles(3), False),
    ])
    def test_is_distance_from_field(self, distance, expected):
        """
        Test is distance from field
        """
        query = QueryBufferDissolveList(
            None, None, distance=distance,
            buffer_type=BufferTypeOption.GEODESIC, fields=(),
            side_option=SideOption.FULL, end_option=EndOption.SQUARE,
            resolution=1, xy_tolerance=None)
        assert query._is_distance_from_field is expected
    # End test_is_distance_from_field method

    @mark.parametrize('distance, expected', [
        (Field('NUM_DIST', data_type=FieldType.real), True),
        (Field('MIX_UNIT', data_type=FieldType.text), False),
        (Meters(5000), False),
        (Miles(3), False),
    ])
    def test_is_numeric_field(self, distance, expected):
        """
        Test is numeric field
        """
        query = QueryBufferDissolveList(
            None, None, distance=distance,
            buffer_type=BufferTypeOption.GEODESIC, fields=(),
            side_option=SideOption.FULL, end_option=EndOption.SQUARE,
            resolution=1, xy_tolerance=None)
        assert query._is_numeric_field is expected
    # End test_is_numeric_field method

    @mark.parametrize('fc_name, distance, expected', [
        ('admin_a', Field('NUM_DIST', data_type=FieldType.real), (False, True)),
        ('admin_a', Field('LIN_UNIT', data_type=FieldType.text), (True, False)),
        ('admin_a', Field('ANG_UNIT', data_type=FieldType.text), (False, True)),
        ('admin_a', Field('MIX_UNIT', data_type=FieldType.text), (True, True)),
        ('admin_a', Meters(5000), (True, False)),
        ('admin_a', DecimalDegrees(0.2), (False, True)),
        ('admin_lcc_na_a', Field('NUM_DIST', data_type=FieldType.real), (True, False)),
    ])
    def test_unit_types(self, buffering, fc_name, distance, expected):
        """
        Test unit types
        """
        source = buffering[fc_name]
        query = QueryBufferDissolveList(
            source, None, distance=distance,
            buffer_type=BufferTypeOption.GEODESIC, fields=(),
            side_option=SideOption.FULL, end_option=EndOption.SQUARE,
            resolution=1, xy_tolerance=None)
        assert query._unit_types == expected
    # End test_unit_types method

    @mark.parametrize('fc_name, distance, expected', [
        ('admin_a', Field('NUM_DIST', data_type=FieldType.real), BufferTypeOption.PLANAR),
        ('admin_a', Field('LIN_UNIT', data_type=FieldType.text), BufferTypeOption.GEODESIC),
        ('admin_a', Field('ANG_UNIT', data_type=FieldType.text), BufferTypeOption.PLANAR),
        ('admin_a', Field('MIX_UNIT', data_type=FieldType.text), BufferTypeOption.GEODESIC),
        ('admin_a', Meters(5000), BufferTypeOption.GEODESIC),
        ('admin_a', DecimalDegrees(0.2), BufferTypeOption.PLANAR),
        ('admin_lcc_na_a', Field('NUM_DIST', data_type=FieldType.real), BufferTypeOption.PLANAR),
    ])
    def test_buffer_type(self, buffering, fc_name, distance, expected):
        """
        Test buffer_type
        """
        source = buffering[fc_name]
        query = QueryBufferDissolveList(
            source, None, distance=distance,
            buffer_type=BufferTypeOption.PLANAR, fields=(),
            side_option=SideOption.FULL, end_option=EndOption.SQUARE,
            resolution=1, xy_tolerance=None)
        assert query.buffer_type == expected
    # End test_buffer_type method

    @mark.parametrize('fc_name, distance, expected', [
        ('admin_a', Field('NUM_DIST', data_type=FieldType.real), ", NUM_DIST || ' degree' AS NUM_DIST"),
        ('admin_a', Field('LIN_UNIT', data_type=FieldType.text), ", LIN_UNIT"),
        ('admin_a', Field('ANG_UNIT', data_type=FieldType.text), ", ANG_UNIT"),
        ('admin_a', Field('MIX_UNIT', data_type=FieldType.text), ", MIX_UNIT"),
        ('admin_a', Meters(5000), ''),
        ('admin_a', DecimalDegrees(0.2), ''),
        ('admin_lcc_na_a', Field('NUM_DIST', data_type=FieldType.real), ", NUM_DIST || ' metre' AS NUM_DIST"),
    ])
    def test_build_distance_field(self, buffering, fc_name, distance, expected):
        """
        Test build_distance_field
        """
        source = buffering[fc_name]
        query = QueryBufferDissolveList(
            source, None, distance=distance,
            buffer_type=BufferTypeOption.PLANAR, fields=(),
            side_option=SideOption.FULL, end_option=EndOption.SQUARE,
            resolution=1, xy_tolerance=None)
        assert query._build_distance_field() == expected
    # End test_build_distance_field method

    def test_get_target_shape_type(self):
        """
        Test _get_target_shape_type
        """
        query = QueryBufferDissolveList(
            None, None, distance=None,
            buffer_type=BufferTypeOption.PLANAR, fields=(),
            side_option=SideOption.FULL, end_option=EndOption.SQUARE,
            resolution=1, xy_tolerance=None)
        assert query._get_target_shape_type() == ShapeType.multi_polygon
    # End test_get_target_shape_type method

    def test_get_unique_fields(self):
        """
        Test _get_unique_fields
        """
        fields = [Field('COUNTRY', data_type=FieldType.text)]
        query = QueryBufferDissolveList(
            None, None, distance=Field('NUM_DIST', data_type=FieldType.real),
            buffer_type=BufferTypeOption.PLANAR, fields=fields,
            side_option=SideOption.FULL, end_option=EndOption.SQUARE,
            resolution=1, xy_tolerance=None)
        assert query._get_unique_fields() == fields
    # End test_get_unique_fields method

    def test_select(self, buffering):
        """
        Test select
        """
        fields = [Field('COUNTRY', data_type=FieldType.text)]
        source = buffering['admin_a']
        query = QueryBufferDissolveList(
            source, None, distance=Meters(5000),
            buffer_type=BufferTypeOption.PLANAR, fields=fields,
            side_option=SideOption.FULL, end_option=EndOption.SQUARE,
            resolution=1, xy_tolerance=None)
        sql = query.select
        assert 'ORDER BY COUNTRY) AS __DRID__, COUNTRY' in sql
    # End test_select method

    def test_select_geometry(self, buffering):
        """
        Test select geometry
        """
        fields = [Field('COUNTRY', data_type=FieldType.text)]
        source = buffering['admin_a']
        query = QueryBufferDissolveList(
            source, None, distance=Field('NUM_DIST', data_type=FieldType.real),
            buffer_type=BufferTypeOption.PLANAR, fields=fields,
            side_option=SideOption.FULL, end_option=EndOption.SQUARE,
            resolution=1, xy_tolerance=None)
        sql = query.select_geometry
        assert "ORDER BY COUNTRY) AS __DRID__, NUM_DIST || ' degree' AS NUM_DIST" in sql
    # End test_select_geometry method
# End TestQueryBufferDissolveList class


class TestQueryBufferDissolveAll:
    """
    Test QueryBufferDissolveAll
    """
    @mark.parametrize('distance, expected', [
        (Field('MIX_UNIT', data_type=FieldType.text), True),
        (Meters(5000), False),
        (Miles(3), False),
    ])
    def test_is_distance_from_field(self, distance, expected):
        """
        Test is distance from field
        """
        query = QueryBufferDissolveAll(
            None, None, distance=distance,
            buffer_type=BufferTypeOption.GEODESIC, fields=(),
            side_option=SideOption.FULL, end_option=EndOption.SQUARE,
            resolution=1, xy_tolerance=None)
        assert query._is_distance_from_field is expected
    # End test_is_distance_from_field method

    @mark.parametrize('distance, expected', [
        (Field('NUM_DIST', data_type=FieldType.real), True),
        (Field('MIX_UNIT', data_type=FieldType.text), False),
        (Meters(5000), False),
        (Miles(3), False),
    ])
    def test_is_numeric_field(self, distance, expected):
        """
        Test is numeric field
        """
        query = QueryBufferDissolveAll(
            None, None, distance=distance,
            buffer_type=BufferTypeOption.GEODESIC, fields=(),
            side_option=SideOption.FULL, end_option=EndOption.SQUARE,
            resolution=1, xy_tolerance=None)
        assert query._is_numeric_field is expected
    # End test_is_numeric_field method

    @mark.parametrize('fc_name, distance, expected', [
        ('admin_a', Field('NUM_DIST', data_type=FieldType.real), (False, True)),
        ('admin_a', Field('LIN_UNIT', data_type=FieldType.text), (True, False)),
        ('admin_a', Field('ANG_UNIT', data_type=FieldType.text), (False, True)),
        ('admin_a', Field('MIX_UNIT', data_type=FieldType.text), (True, True)),
        ('admin_a', Meters(5000), (True, False)),
        ('admin_a', DecimalDegrees(0.2), (False, True)),
        ('admin_lcc_na_a', Field('NUM_DIST', data_type=FieldType.real), (True, False)),
    ])
    def test_unit_types(self, buffering, fc_name, distance, expected):
        """
        Test unit types
        """
        source = buffering[fc_name]
        query = QueryBufferDissolveAll(
            source, None, distance=distance,
            buffer_type=BufferTypeOption.GEODESIC, fields=(),
            side_option=SideOption.FULL, end_option=EndOption.SQUARE,
            resolution=1, xy_tolerance=None)
        assert query._unit_types == expected
    # End test_unit_types method

    @mark.parametrize('fc_name, distance, expected', [
        ('admin_a', Field('NUM_DIST', data_type=FieldType.real), BufferTypeOption.PLANAR),
        ('admin_a', Field('LIN_UNIT', data_type=FieldType.text), BufferTypeOption.GEODESIC),
        ('admin_a', Field('ANG_UNIT', data_type=FieldType.text), BufferTypeOption.PLANAR),
        ('admin_a', Field('MIX_UNIT', data_type=FieldType.text), BufferTypeOption.GEODESIC),
        ('admin_a', Meters(5000), BufferTypeOption.GEODESIC),
        ('admin_a', DecimalDegrees(0.2), BufferTypeOption.PLANAR),
        ('admin_lcc_na_a', Field('NUM_DIST', data_type=FieldType.real), BufferTypeOption.PLANAR),
    ])
    def test_buffer_type(self, buffering, fc_name, distance, expected):
        """
        Test buffer_type
        """
        source = buffering[fc_name]
        query = QueryBufferDissolveAll(
            source, None, distance=distance,
            buffer_type=BufferTypeOption.PLANAR, fields=(),
            side_option=SideOption.FULL, end_option=EndOption.SQUARE,
            resolution=1, xy_tolerance=None)
        assert query.buffer_type == expected
    # End test_buffer_type method

    @mark.parametrize('fc_name, distance, expected', [
        ('admin_a', Field('NUM_DIST', data_type=FieldType.real), ", NUM_DIST || ' degree' AS NUM_DIST"),
        ('admin_a', Field('LIN_UNIT', data_type=FieldType.text), ", LIN_UNIT"),
        ('admin_a', Field('ANG_UNIT', data_type=FieldType.text), ", ANG_UNIT"),
        ('admin_a', Field('MIX_UNIT', data_type=FieldType.text), ", MIX_UNIT"),
        ('admin_a', Meters(5000), ''),
        ('admin_a', DecimalDegrees(0.2), ''),
        ('admin_lcc_na_a', Field('NUM_DIST', data_type=FieldType.real), ", NUM_DIST || ' metre' AS NUM_DIST"),
    ])
    def test_build_distance_field(self, buffering, fc_name, distance, expected):
        """
        Test build_distance_field
        """
        source = buffering[fc_name]
        query = QueryBufferDissolveAll(
            source, None, distance=distance,
            buffer_type=BufferTypeOption.PLANAR, fields=(),
            side_option=SideOption.FULL, end_option=EndOption.SQUARE,
            resolution=1, xy_tolerance=None)
        assert query._build_distance_field() == expected
    # End test_build_distance_field method

    def test_get_target_shape_type(self):
        """
        Test _get_target_shape_type
        """
        query = QueryBufferDissolveAll(
            None, None, distance=None,
            buffer_type=BufferTypeOption.PLANAR, fields=(),
            side_option=SideOption.FULL, end_option=EndOption.SQUARE,
            resolution=1, xy_tolerance=None)
        assert query._get_target_shape_type() == ShapeType.multi_polygon
    # End test_get_target_shape_type method

    def test_get_unique_fields(self):
        """
        Test _get_unique_fields
        """
        fields = [Field('COUNTRY', data_type=FieldType.text)]
        query = QueryBufferDissolveAll(
            None, None, distance=Field('NUM_DIST', data_type=FieldType.real),
            buffer_type=BufferTypeOption.PLANAR, fields=fields,
            side_option=SideOption.FULL, end_option=EndOption.SQUARE,
            resolution=1, xy_tolerance=None)
        assert query._get_unique_fields() == []
    # End test_get_unique_fields method

    def test_select(self):
        """
        Test select
        """
        query = QueryBufferDissolveAll(
            None, None, distance=Meters(5000),
            buffer_type=BufferTypeOption.PLANAR, fields=[],
            side_option=SideOption.FULL, end_option=EndOption.SQUARE,
            resolution=1, xy_tolerance=None)
        assert not query.select
    # End test_select method

    def test_select_geometry(self, buffering):
        """
        Test select geometry
        """
        source = buffering['admin_a']
        query = QueryBufferDissolveAll(
            source, None, distance=Field('NUM_DIST', data_type=FieldType.real),
            buffer_type=BufferTypeOption.PLANAR, fields=[],
            side_option=SideOption.FULL, end_option=EndOption.SQUARE,
            resolution=1, xy_tolerance=None)
        sql = query.select_geometry
        assert 'SELECT geom "[Polygon]", ' in sql
        assert "NUM_DIST || ' degree' AS NUM_DIST" in sql
    # End test_select_geometry method
# End TestQueryBufferDissolveAll class


if __name__ == '__main__':  # pragma: no cover
    pass
