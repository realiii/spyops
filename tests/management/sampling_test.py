# -*- coding: utf-8 -*-
"""
Tests for Sampling
"""


from fudgeo import FeatureClass
from fudgeo.enumeration import ShapeType
from pytest import mark

from spyops.crs.constant import WGS84
from spyops.crs.unit import Feet, Meters
from spyops.environment import Extent, OutputZOption, Setting
from spyops.environment.context import Swap
from spyops.management import (
    generate_points_along_lines,
    generate_rectangles_along_lines, generate_transects_along_lines)
from spyops.shared.enumeration import DistanceTypeOption, PlacementOption

pytestmark = [mark.management, mark.sampling]


class TestGeneratePointsAlongLines:
    """
    Test Generate Points Along Lines
    """

    @mark.parametrize('name, count', [
        ('transmission_m_l', 30),
        ('transmission_zm_l', 30),
        ('transmission_l', 30),
        ('transmission_z_l', 30),
        ('transmission_6654_l', 30),
        ('transmission_6654_m_l', 30),
        ('transmission_6654_z_l', 30),
        ('transmission_6654_zm_l', 30),
        ('transmission_lcc_l', 30),
        ('transmission_lcc_m_l', 30),
        ('transmission_lcc_z_l', 30),
        ('transmission_lcc_zm_l', 30),

        ('transmission_m_ml', 12),
        ('transmission_zm_ml', 12),
        ('transmission_ml', 12),
        ('transmission_z_ml', 12),
        ('transmission_6654_m_ml', 12),
        ('transmission_6654_ml', 12),
        ('transmission_6654_z_ml', 12),
        ('transmission_6654_zm_ml', 12),

        ('hydro_m_a', 30),
        ('hydro_zm_a', 30),
        ('hydro_a', 30),
        ('hydro_z_a', 30),
        ('hydro_6654_a', 30),
        ('hydro_6654_m_a', 30),
        ('hydro_6654_z_a', 30),
        ('hydro_6654_zm_a', 30),
        ('hydro_lcc_a', 30),
        ('hydro_lcc_m_a', 30),
        ('hydro_lcc_z_a', 30),
        ('hydro_lcc_zm_a', 30),

    ])
    @mark.parametrize('include', [
        False,
        True,
    ])
    @mark.parametrize('distance_type', [
        DistanceTypeOption.PLANAR,
        DistanceTypeOption.GEODESIC,
    ])
    def test_percentage(self, mem_gpkg, along_field, name, count, include, distance_type):
        """
        Test percentage
        """
        source = along_field[name]
        where_clause = f'{source.primary_key_field.name} <= 10'
        target = FeatureClass(mem_gpkg, name=f'{name}_points')
        result = generate_points_along_lines(
            source=source, target=target, placement=25,
            placement_option=PlacementOption.PERCENTAGE,
            include_ends=include, distance_type=distance_type,
            where_clause=where_clause)
        assert result.has_z == source.has_z
        assert result.has_m == source.has_m
        assert result.spatial_reference_system.srs_id == source.spatial_reference_system.srs_id
        assert result.shape_type == ShapeType.point
        if include:
            assert len(result) > (count + 2)
        else:
            assert len(result) == count
    # End test_percentage method

    @mark.parametrize('name, linear_count, dd_count', [
        ('transmission_m_l', 150, 171),
        ('transmission_zm_l', 150, 171),
        ('transmission_l', 150, 171),
        ('transmission_z_l', 150, 171),
        ('transmission_6654_l', 150, 171),
        ('transmission_6654_m_l', 150, 171),
        ('transmission_6654_z_l', 150, 171),
        ('transmission_6654_zm_l', 150, 171),
        ('transmission_lcc_l', 150, 171),
        ('transmission_lcc_m_l', 150, 171),
        ('transmission_lcc_z_l', 150, 171),
        ('transmission_lcc_zm_l', 150, 171),

        ('transmission_m_ml', 1477, 1629),
        ('transmission_zm_ml', 1477, 1629),
        ('transmission_ml', 1477, 1629),
        ('transmission_z_ml', 1477, 1629),
        ('transmission_6654_m_ml', 1477, 1629),
        ('transmission_6654_ml', 1477, 1629),
        ('transmission_6654_z_ml', 1477, 1629),
        ('transmission_6654_zm_ml', 1477, 1629),

        ('hydro_m_a', 13, 14),
        ('hydro_zm_a', 13, 14),
        ('hydro_a', 13, 14),
        ('hydro_z_a', 13, 14),
        ('hydro_6654_a', 13, 14),
        ('hydro_6654_m_a', 13, 14),
        ('hydro_6654_z_a', 13, 14),
        ('hydro_6654_zm_a', 13, 14),
        ('hydro_lcc_a', 13, 14),
        ('hydro_lcc_m_a', 13, 14),
        ('hydro_lcc_z_a', 13, 14),
        ('hydro_lcc_zm_a', 13, 14),

    ])
    @mark.parametrize('unit', [
        '200 m',
        '0.002 dd',
    ])
    @mark.parametrize('include', [
        False,
        True,
    ])
    @mark.parametrize('distance_type', [
        DistanceTypeOption.PLANAR,
        DistanceTypeOption.GEODESIC,
    ])
    def test_distance(self, mem_gpkg, along_field, name, linear_count, dd_count, unit, include, distance_type):
        """
        Test distance
        """
        source = along_field[name]
        where_clause = f'{source.primary_key_field.name} <= 10'
        target = FeatureClass(mem_gpkg, name=f'{name}_points')
        result = generate_points_along_lines(
            source=source, target=target, placement=unit,
            placement_option=PlacementOption.DISTANCE,
            include_ends=include, distance_type=distance_type,
            where_clause=where_clause)
        assert result.has_z == source.has_z
        assert result.has_m == source.has_m
        assert result.spatial_reference_system.srs_id == source.spatial_reference_system.srs_id
        assert result.shape_type == ShapeType.point
        if 'm' in unit:
            count = linear_count
        else:
            count = dd_count
        if include:
            assert len(result) > (count + 2)
        else:
            assert len(result) == count
    # End test_distance method

    @mark.parametrize('name, count', [
        ('transmission_m_l', 307),
        ('transmission_zm_l', 406),
        ('transmission_l', 312),
        ('transmission_z_l', 403),
        ('transmission_6654_l', 204),
        ('transmission_6654_m_l', 188),
        ('transmission_6654_z_l', 183),
        ('transmission_6654_zm_l', 166),
        ('transmission_lcc_m_l', 178),
        ('transmission_lcc_z_l', 217),
        ('transmission_lcc_zm_l', 193),

        ('transmission_m_ml', 1085),
        ('transmission_zm_ml', 1085),
        ('transmission_ml', 1085),
        ('transmission_z_ml', 1085),
        ('transmission_6654_m_ml', 1477),
        ('transmission_6654_ml', 1477),
        ('transmission_6654_z_ml', 1477),
        ('transmission_6654_zm_ml', 1477),

        ('hydro_m_a', 21),
        ('hydro_zm_a', 20),
        ('hydro_a', 17),
        ('hydro_z_a', 19),
        ('hydro_6654_a', 14),
        ('hydro_6654_m_a', 15),
        ('hydro_6654_z_a', 15),
        ('hydro_6654_zm_a', 16),
        ('hydro_lcc_a', 16),
        ('hydro_lcc_m_a', 15),
        ('hydro_lcc_z_a', 14),
        ('hydro_lcc_zm_a', 16),

    ])
    @mark.parametrize('include', [
        False,
        True,
    ])
    @mark.parametrize('distance_type', [
        DistanceTypeOption.PLANAR,
        DistanceTypeOption.GEODESIC,
    ])
    def test_field_single_value(self, mem_gpkg, along_field, name, count, include, distance_type):
        """
        Test single value field
        """
        source = along_field[name]
        where_clause = f'{source.primary_key_field.name} <= 10'
        target = FeatureClass(mem_gpkg, name=f'{name}_points')
        result = generate_points_along_lines(
            source=source, target=target, placement='SINGLE_VALUE',
            placement_option=PlacementOption.FIELD,
            include_ends=include, distance_type=distance_type,
            where_clause=where_clause)
        assert result.has_z == source.has_z
        assert result.has_m == source.has_m
        assert result.spatial_reference_system.srs_id == source.spatial_reference_system.srs_id
        assert result.shape_type == ShapeType.point
        if include:
            assert len(result) > (count + 2)
        else:
            assert len(result) == count
    # End test_field_single_value method

    @mark.parametrize('name, count', [
        ('transmission_m_l', 172),
        ('transmission_zm_l', 174),
        ('transmission_l', 222),
        ('transmission_z_l', 218),
        ('transmission_6654_l', 226),
        ('transmission_6654_m_l', 201),
        ('transmission_6654_z_l', 201),
        ('transmission_6654_zm_l', 203),
        ('transmission_lcc_z_l', 224),
        ('transmission_lcc_zm_l', 186),

        ('transmission_m_ml', 1477),
        ('transmission_zm_ml', 1477),
        ('transmission_ml', 1477),
        ('transmission_z_ml', 1477),
        ('transmission_6654_m_ml', 1477),
        ('transmission_6654_ml', 1477),
        ('transmission_6654_z_ml', 1477),
        ('transmission_6654_zm_ml', 1477),

        ('hydro_m_a', 15),
        ('hydro_zm_a', 13),
        ('hydro_a', 15),
        ('hydro_z_a', 16),
        ('hydro_6654_a', 15),
        ('hydro_6654_m_a', 15),
        ('hydro_6654_z_a', 16),
        ('hydro_6654_zm_a', 16),
        ('hydro_lcc_a', 14),
        ('hydro_lcc_m_a', 15),
        ('hydro_lcc_z_a', 15),
        ('hydro_lcc_zm_a', 15),

    ])
    @mark.parametrize('include', [
        False,
        True,
    ])
    @mark.parametrize('distance_type', [
        DistanceTypeOption.PLANAR,
        DistanceTypeOption.GEODESIC,
    ])
    def test_field_single_unit(self, mem_gpkg, along_field, name, count, include, distance_type):
        """
        Test single unit field
        """
        source = along_field[name]
        where_clause = f'{source.primary_key_field.name} <= 10'
        target = FeatureClass(mem_gpkg, name=f'{name}_points')
        result = generate_points_along_lines(
            source=source, target=target, placement='SINGLE_UNIT',
            placement_option=PlacementOption.FIELD,
            include_ends=include, distance_type=distance_type,
            where_clause=where_clause)
        assert result.has_z == source.has_z
        assert result.has_m == source.has_m
        assert result.spatial_reference_system.srs_id == source.spatial_reference_system.srs_id
        assert result.shape_type == ShapeType.point
        if include:
            assert len(result) > (count + 2)
        else:
            assert len(result) == count
    # End test_field_single_unit method

    @mark.parametrize('name, count', [
        ('transmission_m_l', 360),
        ('transmission_zm_l', 313),
        ('transmission_l', 345),
        ('transmission_z_l', 301),
        ('transmission_6654_l', 340),
        ('transmission_6654_m_l', 290),
        ('transmission_6654_z_l', 251),
        ('transmission_6654_zm_l', 254),
        ('transmission_lcc_z_l', 313),
        ('transmission_lcc_zm_l', 331),

        ('transmission_m_ml', 1085),
        ('transmission_zm_ml', 1085),
        ('transmission_ml', 1085),
        ('transmission_z_ml', 1085),
        ('transmission_6654_m_ml', 1085),
        ('transmission_6654_ml', 1085),
        ('transmission_6654_z_ml', 1085),
        ('transmission_6654_zm_ml', 1085),

        ('hydro_m_a', 23),
        ('hydro_zm_a', 22),
        ('hydro_a', 20),
        ('hydro_z_a', 22),
        ('hydro_6654_a', 16),
        ('hydro_6654_m_a', 21),
        ('hydro_6654_z_a', 16),
        ('hydro_6654_zm_a', 24),
        ('hydro_lcc_a', 25),
        ('hydro_lcc_m_a', 27),
        ('hydro_lcc_z_a', 22),
        ('hydro_lcc_zm_a', 20),

    ])
    @mark.parametrize('include', [
        False,
        True,
    ])
    @mark.parametrize('distance_type', [
        DistanceTypeOption.PLANAR,
        DistanceTypeOption.GEODESIC,
    ])
    def test_field_single_dd(self, mem_gpkg, along_field, name, count, include, distance_type):
        """
        Test single dd field
        """
        source = along_field[name]
        where_clause = f'{source.primary_key_field.name} <= 10'
        target = FeatureClass(mem_gpkg, name=f'{name}_points')
        result = generate_points_along_lines(
            source=source, target=target, placement='SINGLE_DD',
            placement_option=PlacementOption.FIELD,
            include_ends=include, distance_type=distance_type,
            where_clause=where_clause)
        assert result.has_z == source.has_z
        assert result.has_m == source.has_m
        assert result.spatial_reference_system.srs_id == source.spatial_reference_system.srs_id
        assert result.shape_type == ShapeType.point
        if include:
            assert len(result) > (count + 2)
        else:
            assert len(result) == count
    # End test_field_single_dd method

    @mark.parametrize('name, count', [
        ('transmission_m_l', 30),
        ('transmission_zm_l', 30),
        ('transmission_l', 30),
        ('transmission_z_l', 30),
        ('transmission_6654_l', 30),
        ('transmission_6654_m_l', 30),
        ('transmission_6654_z_l', 30),
        ('transmission_6654_zm_l', 30),
        ('transmission_lcc_z_l', 30),
        ('transmission_lcc_zm_l', 30),

        ('transmission_m_ml', 12),
        ('transmission_zm_ml', 12),
        ('transmission_ml', 12),
        ('transmission_z_ml', 12),
        ('transmission_6654_m_ml', 12),
        ('transmission_6654_ml', 12),
        ('transmission_6654_z_ml', 12),
        ('transmission_6654_zm_ml', 12),

        ('hydro_m_a', 30),
        ('hydro_zm_a', 30),
        ('hydro_a', 30),
        ('hydro_z_a', 30),
        ('hydro_6654_a', 30),
        ('hydro_6654_m_a', 30),
        ('hydro_6654_z_a', 30),
        ('hydro_6654_zm_a', 30),
        ('hydro_lcc_a', 30),
        ('hydro_lcc_m_a', 30),
        ('hydro_lcc_z_a', 30),
        ('hydro_lcc_zm_a', 30),

    ])
    @mark.parametrize('include', [
        False,
        True,
    ])
    @mark.parametrize('distance_type', [
        DistanceTypeOption.PLANAR,
        DistanceTypeOption.GEODESIC,
    ])
    def test_field_distances(self, mem_gpkg, along_field, name, count, include, distance_type):
        """
        Test distances field
        """
        source = along_field[name]
        where_clause = f'{source.primary_key_field.name} <= 10'
        target = FeatureClass(mem_gpkg, name=f'{name}_points')
        result = generate_points_along_lines(
            source=source, target=target, placement='DISTANCES',
            placement_option=PlacementOption.FIELD,
            include_ends=include, distance_type=distance_type,
            where_clause=where_clause)
        assert result.has_z == source.has_z
        assert result.has_m == source.has_m
        assert result.spatial_reference_system.srs_id == source.spatial_reference_system.srs_id
        assert result.shape_type == ShapeType.point
        if include:
            assert len(result) > (count + 2)
        else:
            assert len(result) == count
    # End test_field_distances method

    @mark.parametrize('placement, option', [
        ('DISTANCES', PlacementOption.FIELD),
        (25, PlacementOption.PERCENTAGE),
        (Meters(20), PlacementOption.DISTANCE),
    ])
    def test_extent(self, mem_gpkg, along_field, placement, option):
        """
        Test distances field
        """
        source = along_field['transmission_6654_l']
        target = FeatureClass(mem_gpkg, name='points')
        result = generate_points_along_lines(
            source=source, target=target, placement=placement,
            placement_option=option, include_ends=False,
            distance_type=DistanceTypeOption.PLANAR)
        count = len(result)
        target = FeatureClass(mem_gpkg, name='some_points')
        with Swap(Setting.EXTENT, Extent.from_bounds(-114.5, 51., -114.25, 51.25, crs=WGS84)):
            result = generate_points_along_lines(
                source=source, target=target, placement=placement,
                placement_option=option, include_ends=False,
                distance_type=DistanceTypeOption.PLANAR)
        assert len(result) < count
        assert len(result) > 0
    # End test_extent method

    @mark.parametrize('placement, option', [
        ('DISTANCES', PlacementOption.FIELD),
        (25, PlacementOption.PERCENTAGE),
        (Meters(20), PlacementOption.DISTANCE),
    ])
    def test_settings(self, mem_gpkg, along_field, placement, option):
        """
        Test distances field
        """
        source = along_field['transmission_6654_l']
        target = FeatureClass(mem_gpkg, name='points')
        with (Swap(Setting.OUTPUT_Z_OPTION, OutputZOption.ENABLED),
              Swap(Setting.OUTPUT_M_OPTION, OutputZOption.ENABLED),
              Swap(Setting.Z_VALUE, 1234),
              Swap(Setting.OUTPUT_COORDINATE_SYSTEM, WGS84)):
            result = generate_points_along_lines(
                source=source, target=target, placement=placement,
                placement_option=option, include_ends=False,
                distance_type=DistanceTypeOption.PLANAR)
            assert len(result) > 0
            assert result.has_z
            assert result.has_m
            assert result.spatial_reference_system.srs_id == 4326
    # End test_extent method
# End TestGeneratePointsAlongLines class


class TestGenerateTransectsAlongLines:
    """
    Test Generate Transects Along Lines
    """
    @mark.parametrize('name, count', [
        ('transmission_m_l', 30),
        ('transmission_zm_l', 30),
        ('transmission_l', 30),
        ('transmission_z_l', 30),
        ('transmission_6654_l', 30),
        ('transmission_6654_m_l', 30),
        ('transmission_6654_z_l', 30),
        ('transmission_6654_zm_l', 30),
        ('transmission_lcc_l', 30),
        ('transmission_lcc_m_l', 30),
        ('transmission_lcc_z_l', 30),
        ('transmission_lcc_zm_l', 30),

        ('transmission_m_ml', 12),
        ('transmission_zm_ml', 12),
        ('transmission_ml', 12),
        ('transmission_z_ml', 12),
        ('transmission_6654_m_ml', 12),
        ('transmission_6654_ml', 12),
        ('transmission_6654_z_ml', 12),
        ('transmission_6654_zm_ml', 12),

        ('hydro_m_a', 30),
        ('hydro_zm_a', 30),
        ('hydro_a', 30),
        ('hydro_z_a', 30),
        ('hydro_6654_a', 30),
        ('hydro_6654_m_a', 30),
        ('hydro_6654_z_a', 30),
        ('hydro_6654_zm_a', 30),
        ('hydro_lcc_a', 30),
        ('hydro_lcc_m_a', 30),
        ('hydro_lcc_z_a', 30),
        ('hydro_lcc_zm_a', 30),

    ])
    @mark.parametrize('include', [
        False,
        True,
    ])
    @mark.parametrize('distance_type', [
        DistanceTypeOption.PLANAR,
        DistanceTypeOption.GEODESIC,
    ])
    def test_percentage(self, mem_gpkg, along_field, name, count, include, distance_type):
        """
        Test percentage
        """
        source = along_field[name]
        where_clause = f'{source.primary_key_field.name} <= 10'
        target = FeatureClass(mem_gpkg, name=f'{name}_points')
        result = generate_transects_along_lines(
            source=source, target=target, placement=25,
            placement_option=PlacementOption.PERCENTAGE,
            include_ends=include, distance_type=distance_type,
            where_clause=where_clause, length=Meters(123))
        assert result.has_z == source.has_z
        assert result.has_m == source.has_m
        assert result.spatial_reference_system.srs_id == source.spatial_reference_system.srs_id
        assert result.shape_type == ShapeType.linestring
        if include:
            assert len(result) > (count + 2)
        else:
            assert len(result) == count
    # End test_percentage method

    @mark.parametrize('name, linear_count, dd_count', [
        ('transmission_m_l', 150, 171),
        ('transmission_zm_l', 150, 171),
        ('transmission_l', 150, 171),
        ('transmission_z_l', 150, 171),
        ('transmission_6654_l', 150, 171),
        ('transmission_6654_m_l', 150, 171),
        ('transmission_6654_z_l', 150, 171),
        ('transmission_6654_zm_l', 150, 171),
        ('transmission_lcc_l', 150, 171),
        ('transmission_lcc_m_l', 150, 171),
        ('transmission_lcc_z_l', 150, 171),
        ('transmission_lcc_zm_l', 150, 171),

        ('transmission_m_ml', 1477, 1629),
        ('transmission_zm_ml', 1477, 1629),
        ('transmission_ml', 1477, 1629),
        ('transmission_z_ml', 1477, 1629),
        ('transmission_6654_m_ml', 1477, 1629),
        ('transmission_6654_ml', 1477, 1629),
        ('transmission_6654_z_ml', 1477, 1629),
        ('transmission_6654_zm_ml', 1477, 1629),

        ('hydro_m_a', 13, 14),
        ('hydro_zm_a', 13, 14),
        ('hydro_a', 13, 14),
        ('hydro_z_a', 13, 14),
        ('hydro_6654_a', 13, 14),
        ('hydro_6654_m_a', 13, 14),
        ('hydro_6654_z_a', 13, 14),
        ('hydro_6654_zm_a', 13, 14),
        ('hydro_lcc_a', 13, 14),
        ('hydro_lcc_m_a', 13, 14),
        ('hydro_lcc_z_a', 13, 14),
        ('hydro_lcc_zm_a', 13, 14),

    ])
    @mark.parametrize('unit', [
        '200 m',
        '0.002 dd',
    ])
    @mark.parametrize('include', [
        False,
        True,
    ])
    @mark.parametrize('distance_type', [
        DistanceTypeOption.PLANAR,
        DistanceTypeOption.GEODESIC,
    ])
    def test_distance(self, mem_gpkg, along_field, name, linear_count, dd_count, unit, include, distance_type):
        """
        Test distance
        """
        source = along_field[name]
        where_clause = f'{source.primary_key_field.name} <= 10'
        target = FeatureClass(mem_gpkg, name=f'{name}_points')
        result = generate_transects_along_lines(
            source=source, target=target, placement=unit,
            placement_option=PlacementOption.DISTANCE,
            include_ends=include, distance_type=distance_type,
            where_clause=where_clause, length=Meters(123))
        assert result.has_z == source.has_z
        assert result.has_m == source.has_m
        assert result.spatial_reference_system.srs_id == source.spatial_reference_system.srs_id
        assert result.shape_type == ShapeType.linestring
        if 'm' in unit:
            count = linear_count
        else:
            count = dd_count
        if include:
            assert len(result) > (count + 2)
        else:
            assert len(result) == count
    # End test_distance method

    @mark.parametrize('name, count', [
        ('transmission_m_l', 307),
        ('transmission_zm_l', 406),
        ('transmission_l', 312),
        ('transmission_z_l', 403),
        ('transmission_6654_l', 204),
        ('transmission_6654_m_l', 188),
        ('transmission_6654_z_l', 183),
        ('transmission_6654_zm_l', 166),
        ('transmission_lcc_m_l', 178),
        ('transmission_lcc_z_l', 217),
        ('transmission_lcc_zm_l', 193),

        ('transmission_m_ml', 1085),
        ('transmission_zm_ml', 1085),
        ('transmission_ml', 1085),
        ('transmission_z_ml', 1085),
        ('transmission_6654_m_ml', 1477),
        ('transmission_6654_ml', 1477),
        ('transmission_6654_z_ml', 1477),
        ('transmission_6654_zm_ml', 1477),

        ('hydro_m_a', 21),
        ('hydro_zm_a', 20),
        ('hydro_a', 17),
        ('hydro_z_a', 19),
        ('hydro_6654_a', 14),
        ('hydro_6654_m_a', 15),
        ('hydro_6654_z_a', 15),
        ('hydro_6654_zm_a', 16),
        ('hydro_lcc_a', 16),
        ('hydro_lcc_m_a', 15),
        ('hydro_lcc_z_a', 14),
        ('hydro_lcc_zm_a', 16),

    ])
    @mark.parametrize('include', [
        False,
        True,
    ])
    @mark.parametrize('distance_type', [
        DistanceTypeOption.PLANAR,
        DistanceTypeOption.GEODESIC,
    ])
    def test_field_single_value(self, mem_gpkg, along_field, name, count, include, distance_type):
        """
        Test single value field
        """
        source = along_field[name]
        where_clause = f'{source.primary_key_field.name} <= 10'
        target = FeatureClass(mem_gpkg, name=f'{name}_points')
        result = generate_transects_along_lines(
            source=source, target=target, placement='SINGLE_VALUE',
            placement_option=PlacementOption.FIELD,
            include_ends=include, distance_type=distance_type,
            where_clause=where_clause, length=Meters(123))
        assert result.has_z == source.has_z
        assert result.has_m == source.has_m
        assert result.spatial_reference_system.srs_id == source.spatial_reference_system.srs_id
        assert result.shape_type == ShapeType.linestring
        if include:
            assert len(result) > (count + 2)
        else:
            assert len(result) == count
    # End test_field_single_value method

    @mark.parametrize('name, count', [
        ('transmission_m_l', 172),
        ('transmission_zm_l', 174),
        ('transmission_l', 222),
        ('transmission_z_l', 218),
        ('transmission_6654_l', 226),
        ('transmission_6654_m_l', 201),
        ('transmission_6654_z_l', 201),
        ('transmission_6654_zm_l', 203),
        ('transmission_lcc_z_l', 224),
        ('transmission_lcc_zm_l', 186),

        ('transmission_m_ml', 1477),
        ('transmission_zm_ml', 1477),
        ('transmission_ml', 1477),
        ('transmission_z_ml', 1477),
        ('transmission_6654_m_ml', 1477),
        ('transmission_6654_ml', 1477),
        ('transmission_6654_z_ml', 1477),
        ('transmission_6654_zm_ml', 1477),

        ('hydro_m_a', 15),
        ('hydro_zm_a', 13),
        ('hydro_a', 15),
        ('hydro_z_a', 16),
        ('hydro_6654_a', 15),
        ('hydro_6654_m_a', 15),
        ('hydro_6654_z_a', 16),
        ('hydro_6654_zm_a', 16),
        ('hydro_lcc_a', 14),
        ('hydro_lcc_m_a', 15),
        ('hydro_lcc_z_a', 15),
        ('hydro_lcc_zm_a', 15),

    ])
    @mark.parametrize('include', [
        False,
        True,
    ])
    @mark.parametrize('distance_type', [
        DistanceTypeOption.PLANAR,
        DistanceTypeOption.GEODESIC,
    ])
    def test_field_single_unit(self, mem_gpkg, along_field, name, count, include, distance_type):
        """
        Test single unit field
        """
        source = along_field[name]
        where_clause = f'{source.primary_key_field.name} <= 10'
        target = FeatureClass(mem_gpkg, name=f'{name}_points')
        result = generate_transects_along_lines(
            source=source, target=target, placement='SINGLE_UNIT',
            placement_option=PlacementOption.FIELD,
            include_ends=include, distance_type=distance_type,
            where_clause=where_clause, length=Meters(123))
        assert result.has_z == source.has_z
        assert result.has_m == source.has_m
        assert result.spatial_reference_system.srs_id == source.spatial_reference_system.srs_id
        assert result.shape_type == ShapeType.linestring
        if include:
            assert len(result) > (count + 2)
        else:
            assert len(result) == count
    # End test_field_single_unit method

    @mark.parametrize('name, count', [
        ('transmission_m_l', 360),
        ('transmission_zm_l', 313),
        ('transmission_l', 345),
        ('transmission_z_l', 301),
        ('transmission_6654_l', 340),
        ('transmission_6654_m_l', 290),
        ('transmission_6654_z_l', 251),
        ('transmission_6654_zm_l', 254),
        ('transmission_lcc_z_l', 313),
        ('transmission_lcc_zm_l', 331),

        ('transmission_m_ml', 1085),
        ('transmission_zm_ml', 1085),
        ('transmission_ml', 1085),
        ('transmission_z_ml', 1085),
        ('transmission_6654_m_ml', 1085),
        ('transmission_6654_ml', 1085),
        ('transmission_6654_z_ml', 1085),
        ('transmission_6654_zm_ml', 1085),

        ('hydro_m_a', 23),
        ('hydro_zm_a', 22),
        ('hydro_a', 20),
        ('hydro_z_a', 22),
        ('hydro_6654_a', 16),
        ('hydro_6654_m_a', 21),
        ('hydro_6654_z_a', 16),
        ('hydro_6654_zm_a', 24),
        ('hydro_lcc_a', 25),
        ('hydro_lcc_m_a', 27),
        ('hydro_lcc_z_a', 22),
        ('hydro_lcc_zm_a', 20),

    ])
    @mark.parametrize('include', [
        False,
        True,
    ])
    @mark.parametrize('distance_type', [
        DistanceTypeOption.PLANAR,
        DistanceTypeOption.GEODESIC,
    ])
    def test_field_single_dd(self, mem_gpkg, along_field, name, count, include, distance_type):
        """
        Test single dd field
        """
        source = along_field[name]
        where_clause = f'{source.primary_key_field.name} <= 10'
        target = FeatureClass(mem_gpkg, name=f'{name}_points')
        result = generate_transects_along_lines(
            source=source, target=target, placement='SINGLE_DD',
            placement_option=PlacementOption.FIELD,
            include_ends=include, distance_type=distance_type,
            where_clause=where_clause, length=Meters(123))
        assert result.has_z == source.has_z
        assert result.has_m == source.has_m
        assert result.spatial_reference_system.srs_id == source.spatial_reference_system.srs_id
        assert result.shape_type == ShapeType.linestring
        if include:
            assert len(result) > (count + 2)
        else:
            assert len(result) == count
    # End test_field_single_dd method

    @mark.parametrize('name, count', [
        ('transmission_m_l', 30),
        ('transmission_zm_l', 30),
        ('transmission_l', 30),
        ('transmission_z_l', 30),
        ('transmission_6654_l', 30),
        ('transmission_6654_m_l', 30),
        ('transmission_6654_z_l', 30),
        ('transmission_6654_zm_l', 30),
        ('transmission_lcc_z_l', 30),
        ('transmission_lcc_zm_l', 30),

        ('transmission_m_ml', 12),
        ('transmission_zm_ml', 12),
        ('transmission_ml', 12),
        ('transmission_z_ml', 12),
        ('transmission_6654_m_ml', 12),
        ('transmission_6654_ml', 12),
        ('transmission_6654_z_ml', 12),
        ('transmission_6654_zm_ml', 12),

        ('hydro_m_a', 30),
        ('hydro_zm_a', 30),
        ('hydro_a', 30),
        ('hydro_z_a', 30),
        ('hydro_6654_a', 30),
        ('hydro_6654_m_a', 30),
        ('hydro_6654_z_a', 30),
        ('hydro_6654_zm_a', 30),
        ('hydro_lcc_a', 30),
        ('hydro_lcc_m_a', 30),
        ('hydro_lcc_z_a', 30),
        ('hydro_lcc_zm_a', 30),

    ])
    @mark.parametrize('include', [
        False,
        True,
    ])
    @mark.parametrize('distance_type', [
        DistanceTypeOption.PLANAR,
        DistanceTypeOption.GEODESIC,
    ])
    def test_field_distances(self, mem_gpkg, along_field, name, count, include, distance_type):
        """
        Test distances field
        """
        source = along_field[name]
        where_clause = f'{source.primary_key_field.name} <= 10'
        target = FeatureClass(mem_gpkg, name=f'{name}_points')
        result = generate_transects_along_lines(
            source=source, target=target, placement='DISTANCES',
            placement_option=PlacementOption.FIELD,
            include_ends=include, distance_type=distance_type,
            where_clause=where_clause, length=Meters(123))
        assert result.has_z == source.has_z
        assert result.has_m == source.has_m
        assert result.spatial_reference_system.srs_id == source.spatial_reference_system.srs_id
        assert result.shape_type == ShapeType.linestring
        if include:
            assert len(result) > (count + 2)
        else:
            assert len(result) == count
    # End test_field_distances method

    @mark.parametrize('placement, option', [
        ('DISTANCES', PlacementOption.FIELD),
        (25, PlacementOption.PERCENTAGE),
        (Meters(20), PlacementOption.DISTANCE),
    ])
    def test_extent(self, mem_gpkg, along_field, placement, option):
        """
        Test distances field
        """
        source = along_field['transmission_6654_l']
        target = FeatureClass(mem_gpkg, name='points')
        result = generate_transects_along_lines(
            source=source, target=target, placement=placement,
            placement_option=option, include_ends=False,
            distance_type=DistanceTypeOption.PLANAR, length=Meters(123))
        count = len(result)
        target = FeatureClass(mem_gpkg, name='some_points')
        with Swap(Setting.EXTENT, Extent.from_bounds(-114.5, 51., -114.25, 51.25, crs=WGS84)):
            result = generate_transects_along_lines(
                source=source, target=target, placement=placement,
                placement_option=option, include_ends=False,
                distance_type=DistanceTypeOption.PLANAR, length=Meters(123))
        assert len(result) < count
        assert len(result) > 0
    # End test_extent method

    @mark.parametrize('placement, option', [
        ('DISTANCES', PlacementOption.FIELD),
        (25, PlacementOption.PERCENTAGE),
        (Meters(20), PlacementOption.DISTANCE),
    ])
    def test_settings(self, mem_gpkg, along_field, placement, option):
        """
        Test distances field
        """
        source = along_field['transmission_6654_l']
        target = FeatureClass(mem_gpkg, name='points')
        with (Swap(Setting.OUTPUT_Z_OPTION, OutputZOption.ENABLED),
              Swap(Setting.OUTPUT_M_OPTION, OutputZOption.ENABLED),
              Swap(Setting.Z_VALUE, 1234),
              Swap(Setting.OUTPUT_COORDINATE_SYSTEM, WGS84)):
            result = generate_transects_along_lines(
                source=source, target=target, placement=placement,
                placement_option=option, include_ends=False,
                distance_type=DistanceTypeOption.PLANAR, length=Meters(123))
            assert len(result) > 0
            assert result.has_z
            assert result.has_m
            assert result.spatial_reference_system.srs_id == 4326
    # End test_extent method
# End TestGenerateTransectsAlongLines class


class TestGenerateRectanglesAlongLines:
    """
    Test Generate Rectangles Along Lines
    """
    @mark.parametrize('name, count', [
        ('transmission_m_l', 27),
        ('transmission_zm_l', 27),
        ('transmission_l', 27),
        ('transmission_z_l', 27),
        ('transmission_6654_l', 27),
        ('transmission_6654_m_l', 27),
        ('transmission_6654_z_l', 27),
        ('transmission_6654_zm_l', 27),
        ('transmission_lcc_l', 27),
        ('transmission_lcc_m_l', 27),
        ('transmission_lcc_z_l', 27),
        ('transmission_lcc_zm_l', 27),

        ('transmission_m_ml', 12),
        ('transmission_zm_ml', 12),
        ('transmission_ml', 12),
        ('transmission_z_ml', 12),
        ('transmission_6654_m_ml', 12),
        ('transmission_6654_ml', 12),
        ('transmission_6654_z_ml', 12),
        ('transmission_6654_zm_ml', 12),

        ('hydro_m_a', 20),
        ('hydro_zm_a', 20),
        ('hydro_a', 20),
        ('hydro_z_a', 20),
        ('hydro_6654_a', 20),
        ('hydro_6654_m_a', 20),
        ('hydro_6654_z_a', 20),
        ('hydro_6654_zm_a', 20),
        ('hydro_lcc_a', 20),
        ('hydro_lcc_m_a', 20),
        ('hydro_lcc_z_a', 20),
        ('hydro_lcc_zm_a', 20),

    ])
    @mark.parametrize('include', [
        False,
        True,
    ])
    @mark.parametrize('distance_type', [
        DistanceTypeOption.PLANAR,
        DistanceTypeOption.GEODESIC,
    ])
    def test_percentage(self, mem_gpkg, along_field, name, count, include, distance_type):
        """
        Test percentage
        """
        source = along_field[name]
        where_clause = f'{source.primary_key_field.name} <= 10'
        target = FeatureClass(mem_gpkg, name=f'{name}_points')
        result = generate_rectangles_along_lines(
            source=source, target=target, placement=25,
            placement_option=PlacementOption.PERCENTAGE,
            include_ends=include, distance_type=distance_type,
            where_clause=where_clause, length=Meters(123), width=Feet(123))
        assert result.has_z == source.has_z
        assert result.has_m == source.has_m
        assert result.spatial_reference_system.srs_id == source.spatial_reference_system.srs_id
        assert result.shape_type == ShapeType.polygon
        if include:
            assert len(result) > (count + 2)
        else:
            assert len(result) == count
    # End test_percentage method

    @mark.parametrize('name, linear_count, dd_count', [
        ('transmission_m_l', 148, 162),
        ('transmission_zm_l', 148, 162),
        ('transmission_l', 148, 162),
        ('transmission_z_l', 148, 162),
        ('transmission_6654_l', 148, 162),
        ('transmission_6654_m_l', 148, 162),
        ('transmission_6654_z_l', 148, 162),
        ('transmission_6654_zm_l', 148, 162),

        ('transmission_m_ml', 1473, 1626),
        ('transmission_zm_ml', 1473, 1626),
        ('transmission_ml', 1473, 1626),
        ('transmission_z_ml', 1473, 1626),
        ('transmission_6654_m_ml', 1473, 1626),
        ('transmission_6654_ml', 1473, 1626),
        ('transmission_6654_z_ml', 1473, 1626),
        ('transmission_6654_zm_ml', 1473, 1626),

        ('hydro_m_a', 5, 5),
        ('hydro_zm_a', 5, 5),
        ('hydro_a', 5, 5),
        ('hydro_z_a', 5, 5),
        ('hydro_6654_a', 5, 5),
        ('hydro_6654_m_a', 5, 5),
        ('hydro_6654_z_a', 5, 5),
        ('hydro_6654_zm_a', 5, 5),
        ('hydro_lcc_a', 5, 5),
        ('hydro_lcc_m_a', 5, 5),
        ('hydro_lcc_z_a', 5, 5),
        ('hydro_lcc_zm_a', 5, 5),

    ])
    @mark.parametrize('unit', [
        '200 m',
        '0.002 dd',
    ])
    @mark.parametrize('include', [
        False,
        True,
    ])
    @mark.parametrize('distance_type', [
        DistanceTypeOption.PLANAR,
        DistanceTypeOption.GEODESIC,
    ])
    def test_distance(self, mem_gpkg, along_field, name, linear_count, dd_count, unit, include, distance_type):
        """
        Test distance
        """
        source = along_field[name]
        where_clause = f'{source.primary_key_field.name} <= 10'
        target = FeatureClass(mem_gpkg, name=f'{name}_points')
        result = generate_rectangles_along_lines(
            source=source, target=target, placement=unit,
            placement_option=PlacementOption.DISTANCE,
            include_ends=include, distance_type=distance_type,
            where_clause=where_clause, length=Meters(123), width=Feet(123))
        assert result.has_z == source.has_z
        assert result.has_m == source.has_m
        assert result.spatial_reference_system.srs_id == source.spatial_reference_system.srs_id
        assert result.shape_type == ShapeType.polygon
        if 'm' in unit:
            count = linear_count
        else:
            count = dd_count
        if include:
            assert len(result) > (count + 2)
        else:
            assert len(result) == count
    # End test_distance method

    @mark.parametrize('name, count', [
        ('transmission_m_l', 294),
        ('transmission_zm_l', 392),
        ('transmission_l', 299),
        ('transmission_z_l', 391),
        ('transmission_6654_l', 199),
        ('transmission_6654_m_l', 184),
        ('transmission_6654_z_l', 179),
        ('transmission_6654_zm_l', 161),
        ('transmission_lcc_m_l', 173),
        ('transmission_lcc_z_l', 211),
        ('transmission_lcc_zm_l', 187),

        ('transmission_m_ml', 1083),
        ('transmission_zm_ml', 1083),
        ('transmission_ml', 1083),
        ('transmission_z_ml', 1083),
        ('transmission_6654_m_ml', 1473),
        ('transmission_6654_ml', 1473),
        ('transmission_6654_z_ml', 1473),
        ('transmission_6654_zm_ml', 1473),

        ('hydro_m_a', 12),
        ('hydro_zm_a', 10),
        ('hydro_a', 8),
        ('hydro_z_a', 9),
        ('hydro_6654_a', 6),
        ('hydro_6654_m_a', 7),
        ('hydro_6654_z_a', 7),
        ('hydro_6654_zm_a', 6),
        ('hydro_lcc_a', 7),
        ('hydro_lcc_m_a', 6),
        ('hydro_lcc_z_a', 5),
        ('hydro_lcc_zm_a', 7),

    ])
    @mark.parametrize('include', [
        False,
        True,
    ])
    @mark.parametrize('distance_type', [
        DistanceTypeOption.PLANAR,
        DistanceTypeOption.GEODESIC,
    ])
    def test_field_single_value(self, mem_gpkg, along_field, name, count, include, distance_type):
        """
        Test single value field
        """
        source = along_field[name]
        where_clause = f'{source.primary_key_field.name} <= 10'
        target = FeatureClass(mem_gpkg, name=f'{name}_points')
        result = generate_rectangles_along_lines(
            source=source, target=target, placement='SINGLE_VALUE',
            placement_option=PlacementOption.FIELD,
            include_ends=include, distance_type=distance_type,
            where_clause=where_clause, length=Meters(123), width=Feet(123))
        assert result.has_z == source.has_z
        assert result.has_m == source.has_m
        assert result.spatial_reference_system.srs_id == source.spatial_reference_system.srs_id
        assert result.shape_type == ShapeType.polygon
        if include:
            assert len(result) > (count + 2)
        else:
            assert len(result) == count
    # End test_field_single_value method

    @mark.parametrize('name, count', [
        ('transmission_m_l', 168),
        ('transmission_zm_l', 169),
        ('transmission_l', 217),
        ('transmission_z_l', 213),
        ('transmission_6654_l', 220),
        ('transmission_6654_z_l', 197),
        ('transmission_6654_zm_l', 198),

        ('transmission_m_ml', 1473),
        ('transmission_zm_ml', 1473),
        ('transmission_ml', 1473),
        ('transmission_z_ml', 1473),
        ('transmission_6654_m_ml', 1473),
        ('transmission_6654_ml', 1473),
        ('transmission_6654_z_ml', 1473),
        ('transmission_6654_zm_ml', 1473),

        ('hydro_m_a', 7),
        ('hydro_zm_a', 5),
        ('hydro_a', 7),
        ('hydro_z_a', 8),
        ('hydro_6654_a', 7),
        ('hydro_6654_m_a', 6),
        ('hydro_6654_z_a', 7),
        ('hydro_6654_zm_a', 7),
        ('hydro_lcc_a', 7),
        ('hydro_lcc_m_a', 6),
        ('hydro_lcc_z_a', 6),
        ('hydro_lcc_zm_a', 6),

    ])
    @mark.parametrize('include', [
        False,
        True,
    ])
    @mark.parametrize('distance_type', [
        DistanceTypeOption.PLANAR,
        DistanceTypeOption.GEODESIC,
    ])
    def test_field_single_unit(self, mem_gpkg, along_field, name, count, include, distance_type):
        """
        Test single unit field
        """
        source = along_field[name]
        where_clause = f'{source.primary_key_field.name} <= 10'
        target = FeatureClass(mem_gpkg, name=f'{name}_points')
        result = generate_rectangles_along_lines(
            source=source, target=target, placement='SINGLE_UNIT',
            placement_option=PlacementOption.FIELD,
            include_ends=include, distance_type=distance_type,
            where_clause=where_clause, length=Meters(123), width=Feet(123))
        assert result.has_z == source.has_z
        assert result.has_m == source.has_m
        assert result.spatial_reference_system.srs_id == source.spatial_reference_system.srs_id
        assert result.shape_type == ShapeType.polygon
        if include:
            assert len(result) > (count + 2)
        else:
            assert len(result) == count
    # End test_field_single_unit method

    @mark.parametrize('name, count', [
        ('transmission_m_l', 348),
        ('transmission_zm_l', 302),
        ('transmission_l', 333),
        ('transmission_z_l', 289),
        ('transmission_6654_l', 328),
        ('transmission_6654_m_l', 278),
        ('transmission_6654_z_l', 239),
        ('transmission_6654_zm_l', 245),
        ('transmission_lcc_z_l', 302),
        ('transmission_lcc_zm_l', 318),

        ('transmission_m_ml', 1083),
        ('transmission_zm_ml', 1083),
        ('transmission_ml', 1083),
        ('transmission_z_ml', 1083),
        ('transmission_6654_m_ml', 1083),
        ('transmission_6654_ml', 1083),
        ('transmission_6654_z_ml', 1083),
        ('transmission_6654_zm_ml', 1083),

        ('hydro_m_a', 10),
        ('hydro_zm_a', 10),
        ('hydro_a', 10),
        ('hydro_z_a', 11),
        ('hydro_6654_a', 8),
        ('hydro_6654_m_a', 10),
        ('hydro_6654_z_a', 7),
        ('hydro_6654_zm_a', 12),
        ('hydro_lcc_a', 12),
        ('hydro_lcc_m_a', 13),
        ('hydro_lcc_z_a', 10),
        ('hydro_lcc_zm_a', 10),

    ])
    @mark.parametrize('include', [
        False,
        True,
    ])
    @mark.parametrize('distance_type', [
        DistanceTypeOption.PLANAR,
        DistanceTypeOption.GEODESIC,
    ])
    def test_field_single_dd(self, mem_gpkg, along_field, name, count, include, distance_type):
        """
        Test single dd field
        """
        source = along_field[name]
        where_clause = f'{source.primary_key_field.name} <= 10'
        target = FeatureClass(mem_gpkg, name=f'{name}_points')
        result = generate_rectangles_along_lines(
            source=source, target=target, placement='SINGLE_DD',
            placement_option=PlacementOption.FIELD,
            include_ends=include, distance_type=distance_type,
            where_clause=where_clause, length=Meters(123), width=Feet(123))
        assert result.has_z == source.has_z
        assert result.has_m == source.has_m
        assert result.spatial_reference_system.srs_id == source.spatial_reference_system.srs_id
        assert result.shape_type == ShapeType.polygon
        if include:
            assert len(result) > (count + 2)
        else:
            assert len(result) == count
    # End test_field_single_dd method

    @mark.parametrize('name, count', [
        ('transmission_m_l', 28),
        ('transmission_zm_l', 28),
        ('transmission_l', 28),
        ('transmission_z_l', 28),
        ('transmission_6654_l', 28),
        ('transmission_6654_m_l', 28),
        ('transmission_6654_z_l', 28),
        ('transmission_6654_zm_l', 28),
        ('transmission_lcc_z_l', 28),
        ('transmission_lcc_zm_l', 28),

        ('transmission_m_ml', 12),
        ('transmission_zm_ml', 12),
        ('transmission_ml', 12),
        ('transmission_z_ml', 12),
        ('transmission_6654_m_ml', 12),
        ('transmission_6654_ml', 12),
        ('transmission_6654_z_ml', 12),
        ('transmission_6654_zm_ml', 12),

        ('hydro_m_a', 23),
        ('hydro_a', 23),
        ('hydro_6654_a', 23),
        ('hydro_6654_m_a', 23),
        ('hydro_lcc_a', 23),

    ])
    @mark.parametrize('include', [
        False,
        True,
    ])
    @mark.parametrize('distance_type', [
        DistanceTypeOption.PLANAR,
        DistanceTypeOption.GEODESIC,
    ])
    def test_field_distances(self, mem_gpkg, along_field, name, count, include, distance_type):
        """
        Test distances field
        """
        source = along_field[name]
        where_clause = f'{source.primary_key_field.name} <= 10'
        target = FeatureClass(mem_gpkg, name=f'{name}_points')
        result = generate_rectangles_along_lines(
            source=source, target=target, placement='DISTANCES',
            placement_option=PlacementOption.FIELD,
            include_ends=include, distance_type=distance_type,
            where_clause=where_clause, length=Meters(123), width=Feet(123))
        assert result.has_z == source.has_z
        assert result.has_m == source.has_m
        assert result.spatial_reference_system.srs_id == source.spatial_reference_system.srs_id
        assert result.shape_type == ShapeType.polygon
        if include:
            assert len(result) > (count + 2)
        else:
            assert len(result) == count
    # End test_field_distances method

    @mark.parametrize('placement, option', [
        ('DISTANCES', PlacementOption.FIELD),
        (25, PlacementOption.PERCENTAGE),
        (Meters(20), PlacementOption.DISTANCE),
    ])
    def test_extent(self, mem_gpkg, along_field, placement, option):
        """
        Test distances field
        """
        source = along_field['transmission_6654_l']
        target = FeatureClass(mem_gpkg, name='points')
        result = generate_rectangles_along_lines(
            source=source, target=target, placement=placement,
            placement_option=option, include_ends=False,
            distance_type=DistanceTypeOption.PLANAR, length=Meters(123), width=Feet(123))
        count = len(result)
        target = FeatureClass(mem_gpkg, name='some_points')
        with Swap(Setting.EXTENT, Extent.from_bounds(-114.5, 51., -114.25, 51.25, crs=WGS84)):
            result = generate_rectangles_along_lines(
                source=source, target=target, placement=placement,
                placement_option=option, include_ends=False,
                distance_type=DistanceTypeOption.PLANAR, length=Meters(123), width=Feet(123))
        assert len(result) < count
        assert len(result) > 0
    # End test_extent method

    @mark.parametrize('placement, option', [
        ('DISTANCES', PlacementOption.FIELD),
        (25, PlacementOption.PERCENTAGE),
        (Meters(20), PlacementOption.DISTANCE),
    ])
    def test_settings(self, mem_gpkg, along_field, placement, option):
        """
        Test distances field
        """
        source = along_field['transmission_6654_l']
        target = FeatureClass(mem_gpkg, name='points')
        with (Swap(Setting.OUTPUT_Z_OPTION, OutputZOption.ENABLED),
              Swap(Setting.OUTPUT_M_OPTION, OutputZOption.ENABLED),
              Swap(Setting.Z_VALUE, 1234),
              Swap(Setting.OUTPUT_COORDINATE_SYSTEM, WGS84)):
            result = generate_rectangles_along_lines(
                source=source, target=target, placement=placement,
                placement_option=option, include_ends=False,
                distance_type=DistanceTypeOption.PLANAR, length=Meters(123), width=Feet(123))
            assert len(result) > 0
            assert result.has_z
            assert result.has_m
            assert result.spatial_reference_system.srs_id == 4326
    # End test_extent method
# End TestGenerateRectanglesAlongLines class


if __name__ == '__main__':  # pragma: no cover
    pass
