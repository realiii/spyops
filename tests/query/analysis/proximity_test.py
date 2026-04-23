# -*- coding: utf-8 -*-
"""
Test for Proximity Query classes
"""


from fudgeo import FeatureClass, Field
from fudgeo.enumeration import FieldType, ShapeType
from pyproj import CRS
from pytest import mark, approx

from spyops.crs.enumeration import DistanceUnit
from spyops.crs.unit import DecimalDegrees, Meters, Miles
from spyops.environment import Extent, Setting
from spyops.environment.context import Swap
from spyops.query.analysis.proximity import (
    QueryBufferDissolveAll, QueryBufferDissolveList, QueryBufferDissolveNone,
    QueryCreateThiessenPolygons, QueryMultipleBuffer)
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


class TestQueryBufferDissolveNone:
    """
    Test QueryBufferDissolveNone
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
        query = QueryBufferDissolveNone(
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
        query = QueryBufferDissolveNone(
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
        query = QueryBufferDissolveNone(
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
        query = QueryBufferDissolveNone(
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
        query = QueryBufferDissolveNone(
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
        query = QueryBufferDissolveNone(
            None, None, distance=None,
            buffer_type=BufferTypeOption.PLANAR, fields=(),
            side_option=SideOption.FULL, end_option=EndOption.SQUARE,
            resolution=1, xy_tolerance=None)
        assert query._get_target_shape_type() == ShapeType.multi_polygon
    # End test_get_target_shape_type method

    def test_get_unique_fields(self, buffering):
        """
        Test _get_unique_fields
        """
        fields = [Field('COUNTRY', data_type=FieldType.text)]
        source = buffering['admin_a']
        query = QueryBufferDissolveNone(
            source, None, distance=Field('NUM_DIST', data_type=FieldType.real),
            buffer_type=BufferTypeOption.PLANAR, fields=fields,
            side_option=SideOption.FULL, end_option=EndOption.SQUARE,
            resolution=1, xy_tolerance=None)
        assert [f.name for f in query._get_unique_fields()] == [
            'ORIG_FID', 'FEATURE_ID', 'PART_ID', 'COUNTRY', 'ISO_CODE',
            'ISO_CC', 'ISO_SUB', 'ADMINTYPE', 'CONTINENT', 'LAND_TYPE',
            'LAND_RANK', 'NUM_DIST', 'LIN_UNIT', 'ANG_UNIT', 'MIX_UNIT']
    # End test_get_unique_fields method

    def test_select(self, buffering):
        """
        Test select
        """
        fields = [Field('COUNTRY', data_type=FieldType.text)]
        source = buffering['admin_a']
        query = QueryBufferDissolveNone(
            source, None, distance=Meters(5000),
            buffer_type=BufferTypeOption.PLANAR, fields=fields,
            side_option=SideOption.FULL, end_option=EndOption.SQUARE,
            resolution=1, xy_tolerance=None)
        sql = query.select
        assert 'SELECT fid, fid, FEATURE_ID, PART_ID, COUNTRY, ISO_CODE, ' in sql
    # End test_select method

    def test_select_geometry(self, buffering):
        """
        Test select geometry
        """
        fields = [Field('COUNTRY', data_type=FieldType.text)]
        source = buffering['admin_a']
        query = QueryBufferDissolveNone(
            source, None, distance=Field('NUM_DIST', data_type=FieldType.real),
            buffer_type=BufferTypeOption.PLANAR, fields=fields,
            side_option=SideOption.FULL, end_option=EndOption.SQUARE,
            resolution=1, xy_tolerance=None)
        sql = query.select_geometry
        assert 'SELECT geom "[Polygon]", fid, NUM_DIST || ' in sql
    # End test_select_geometry method
# End TestQueryBufferDissolveNone class


class TestQueryMultipleBuffer:
    """
    Test Query Multiple Buffer
    """
    def test_iteration(self, mem_gpkg, buffering):
        """
        Test iteration
        """
        source = buffering['mb_boxes_a']
        target = FeatureClass(mem_gpkg, 'mb_boxes_buffer_a')
        query = QueryMultipleBuffer(
            source=source, target=target, distance_unit=DistanceUnit.METERS,
            distances=[10, 20, 30], buffer_type=BufferTypeOption.GEODESIC,
            field_name='distance'
        )
        queries, updates = zip(*query)
        assert len(queries) == 3
        assert len(updates) == 3
        update, *_ = updates
        assert '30.0 meters' in update
    # End test_iteration method

    def test_make_update_sql(self, mem_gpkg, buffering):
        """
        Test make update sql
        """
        source = buffering['mb_boxes_a']
        target = FeatureClass(mem_gpkg, 'mb_boxes_buffer_a')
        query = QueryMultipleBuffer(
            source=source, target=target, distance_unit=DistanceUnit.METERS,
            distances=[10, 20, 30], buffer_type=BufferTypeOption.GEODESIC,
            field_name='distance'
        )
        assert query._make_update_sql(Meters(10))

        query = QueryMultipleBuffer(
            source=source, target=target, distance_unit=DistanceUnit.METERS,
            distances=[10, 20, 30], buffer_type=BufferTypeOption.GEODESIC,
        )
        assert not query._make_update_sql(Meters(10))
    # End test_make_update_sql method

    @mark.parametrize('fc_name, overlap, only, distances, expected', [
        ('mb_boxes_a', True, False, [-10, 0, 20, 30], ['-10.0 meters', '0.0 meters', '20.0 meters', '30.0 meters']),
        ('mb_boxes_a', True, True, [-10, 20, 30], ['-10.0 meters', '20.0 meters', '30.0 meters']),
        ('mb_boxes_a', True, False, [-10, 20, 30], ['-10.0 meters', '', '20.0 meters', '30.0 meters']),
        ('mb_boxes_a', False, True, [-10, 20, 30], ['-10.0 meters', '20.0 meters', '30.0 meters']),
        ('mb_boxes_a', False, False, [-10, 20, 30], ['-10.0 meters', '0.0 meters', '20.0 meters', '30.0 meters']),
        ('mb_lines_l', True, True, [-10, 20, 30], ['20.0 meters', '30.0 meters']),
        ('mb_lines_l', True, False, [-10, 20, 30], ['20.0 meters', '30.0 meters']),
        ('mb_lines_l', False, True, [-10, 20, 30], ['20.0 meters', '30.0 meters']),
        ('mb_lines_l', False, False, [-10, 20, 30], ['20.0 meters', '30.0 meters']),
        ('mb_points_p', True, True, [-10, 20, 30], ['20.0 meters', '30.0 meters']),
        ('mb_points_p', True, False, [-10, 20, 30], ['20.0 meters', '30.0 meters']),
        ('mb_points_p', False, True, [-10, 20, 30], ['20.0 meters', '30.0 meters']),
        ('mb_points_p', False, False, [-10, 20, 30], ['20.0 meters', '30.0 meters']),
    ])
    def test_distances_and_labels(self, mem_gpkg, buffering, fc_name, overlap,
                                  only, distances, expected):
        """
        Test distances and labels
        """
        source = buffering[fc_name]
        target = FeatureClass(mem_gpkg, 'buffer_a')
        query = QueryMultipleBuffer(
            source=source, target=target, distance_unit=DistanceUnit.METERS,
            distances=distances, buffer_type=BufferTypeOption.GEODESIC,
            overlapping=overlap, only_outside=only,
        )
        _, labels = query._distances_and_labels()
        assert labels == expected
    # End test_distances_and_labels method

    @mark.parametrize('overlap', [
        True, False,
    ])
    def test_sql(self, mem_gpkg, buffering, overlap):
        """
        Test insert select and select geometry
        """
        source = buffering['mb_boxes_a']
        target = FeatureClass(mem_gpkg, 'mb_boxes_buffer_a')
        query = QueryMultipleBuffer(
            source=source, target=target, distance_unit=DistanceUnit.METERS,
            distances=[10, 20, 30], buffer_type=BufferTypeOption.GEODESIC,
            overlapping=overlap,
        )
        assert source.name in query.select
        assert 'geom "[Polygon]"' in query.select_geometry
        assert target.name in query.insert
    # End test_sql method

    @mark.parametrize('fc_name, only, option', [
        ('mb_boxes_a', True, SideOption.ONLY_OUTSIDE),
        ('mb_boxes_a', False, SideOption.FULL),
        ('mb_lines_l', True, SideOption.FULL),
        ('mb_lines_l', False, SideOption.FULL),
        ('mb_points_p', True, SideOption.FULL),
        ('mb_points_p', False, SideOption.FULL),
    ])
    def test_get_side_option(self, buffering, fc_name, only, option):
        """
        Test get side option
        """
        source = buffering[fc_name]
        query = QueryMultipleBuffer(
            source=source, target=None, distance_unit=DistanceUnit.METERS,
            distances=[10, 20, 30], buffer_type=BufferTypeOption.GEODESIC,
            only_outside=only,
        )
        assert query._get_side_option(source, only) == option
    # End test_get_side_option method

    @mark.parametrize('overlap, field_name, expected', [
        (True, 'distance', ['ORIG_FID', 'FEATURE_ID', 'distance']),
        (False, 'distance', ['distance']),
        (True, None, ['ORIG_FID', 'FEATURE_ID']),
        (False, None, []),
    ])
    def test_get_unique_fields(self, buffering, overlap, field_name, expected):
        """
        Test get unique fields
        """
        source = buffering['mb_boxes_a']
        query = QueryMultipleBuffer(
            source=source, target=None, distance_unit=DistanceUnit.METERS,
            distances=[10, 20, 30], buffer_type=BufferTypeOption.GEODESIC,
            overlapping=overlap, field_name=field_name,
        )
        fields = query._get_unique_fields()
        assert [f.name for f in fields] == expected
    # End test_get_unique_fields method
# End TestQueryMultipleBuffer class


class TestQueryCreateThiessenPolygons:
    """
    Test QueryCreateThiessenPolygons
    """
    def test_get_target_shape_type(self):
        """
        Test get target shape type
        """
        query = QueryCreateThiessenPolygons(
            None, target=None, include_attributes=True, xy_tolerance=None)
        assert query._get_target_shape_type() == ShapeType.polygon
    # End test_get_target_shape_type method

    @mark.parametrize('include, names', [
        (True, ['ORIG_FID', 'FEATURE_ID', 'PART_ID', 'NAME', 'COUNTRY', 'ISO_CODE', 'ISO_CC', 'ISO_SUB', 'ADMINTYPE', 'DISPUTED', 'NOTES', 'AUTONOMOUS', 'COUNTRYAFF', 'CONTINENT', 'LAND_TYPE', 'LAND_RANK']),
        (False, ['ORIG_FID']),
    ])
    def test_unique_fields(self, world_features, include, names):
        """
        Test get target shape type
        """
        source = world_features['admin_a']
        query = QueryCreateThiessenPolygons(
            source, target=None, include_attributes=include, xy_tolerance=None)
        fields = query._get_unique_fields()
        assert [f.name for f in fields] == names
    # End test_unique_fields method

    def test_extent_analysis(self, world_features):
        """
        Test extent from analysis setting
        """
        source = world_features['admin_a']
        extent = Extent.from_bounds(-115, 50, -110, 55, crs=CRS(4326))
        with Swap(Setting.EXTENT, extent):
            query = QueryCreateThiessenPolygons(
                source, target=None, include_attributes=False,
                xy_tolerance=None)
            assert query.extent.bounds == (-115.0, 50.0, -110.0, 55.0)
    # End test_extent_analysis method

    def test_extent_source(self, world_features):
        """
        Test extent from analysis setting
        """
        source = world_features['admin_a']
        query = QueryCreateThiessenPolygons(
            source, target=None, include_attributes=False,
            xy_tolerance=None)
        assert approx(query.extent.bounds, abs=0.001) == (
            -197.9999, -98.6832, 197.9999, 92.3487)
    # End test_extent_source method

    @mark.parametrize('include, content', [
        (True, 'SELECT SHAPE "[Polygon]", fid, FEATURE_ID, PART_ID, NAME'),
        (False, 'SELECT SHAPE "[Polygon]", fid\n'),
    ])
    def test_select(self, world_features, include, content):
        """
        Test select
        """
        source = world_features['admin_a']
        query = QueryCreateThiessenPolygons(
            source, target=None, include_attributes=include, xy_tolerance=None)
        assert content in query.select
    # End test_select method

    def test_zm_config(self, world_features):
        """
        Test ZM Config
        """
        source = world_features['admin_a']
        query = QueryCreateThiessenPolygons(
            source, target=None, include_attributes=False,
            xy_tolerance=None)
        assert query.zm_config == (False, False, False)
    # End test_zm_config method
# End TestQueryCreateThiessenPolygons class


if __name__ == '__main__':  # pragma: no cover
    pass
