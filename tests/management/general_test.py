# -*- coding: utf-8 -*-
"""
Tests for General Data Management
"""


from fudgeo import FeatureClass, Table
from pyproj import CRS
from pytest import mark

from spyops.environment import Extent, Setting
from spyops.environment.context import Swap
from spyops.management import copy, delete, find_identical, rename
from spyops.shared.field import ORIG_FID, REASON, REPEAT_FID

pytestmark = [mark.management, mark.general]


def test_copy(ntdb_zm_small, mem_gpkg):
    """
    Test copy function
    """
    source = ntdb_zm_small['hydro_zm_a']
    target_name = 'hydro_a_copy'
    with Swap(Setting.CURRENT_WORKSPACE, mem_gpkg):
        result = copy(source, target_name)
    assert result is not None
    assert isinstance(result, FeatureClass)
    assert result.name == target_name
    assert len(result) == len(source)
    assert result.has_z == source.has_z
    assert result.has_m == source.has_m
    assert result.spatial_reference_system == source.spatial_reference_system
# End test_copy function


def test_delete(ntdb_zm_small, mem_gpkg):
    """
    Test delete function
    """
    source = ntdb_zm_small['hydro_zm_a']
    target_name = 'hydro_a_copy'
    with Swap(Setting.CURRENT_WORKSPACE, mem_gpkg):
        result = copy(source, target_name)
        result = delete([result])
        assert result is True
        result = copy(source, target_name)
        result = delete([result] * 2)
        assert result is True
        result = delete([])
        assert result is False
# End test_delete function


def test_rename(ntdb_zm_small, mem_gpkg):
    """
    Test rename function
    """
    source = ntdb_zm_small['hydro_zm_a']
    target_name = 'hydro_a_copy'
    with Swap(Setting.CURRENT_WORKSPACE, mem_gpkg):
        copy(source, target_name)
        name = 'hydro_a_copy_2'
        rename(target_name, name)
        assert isinstance(mem_gpkg[name], FeatureClass)
# End test_rename function


class TestFindIdentical:
    """
    Test Find Identical
    """
    @mark.parametrize('fc_name, include, expected', [
        ('point_p', True, [
            (2, 3),
            (4, 5), (4, 6),
            (7, 8), (7, 9), (7, 10),
            (11, 12), (11, 13), (11, 14), (11, 15)]),
        ('point_p', False, [
            (16, 17), (16, 18), (16, 19), (16, 20),
            (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8),
            (1, 9), (1, 10), (1, 11), (1, 12), (1, 13), (1, 14), (1, 15)]),
        ('multipoint_mp', True, [
            (34, 35),  (34, 36), (34, 37), (34, 38),
            (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8),
            (9, 10), (9, 11), (9, 12), (9, 13), (9, 14), (9, 15),
            (16, 17), (16, 18), (16, 19), (16, 20), (16, 21),
            (22, 23), (22, 24), (22, 25), (22, 26),
            (27, 28), (27, 29), (27, 30)]),
        ('multipoint_mp', False, [
            (34, 35),  (34, 36), (34, 37), (34, 38),
            (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8),
            (9, 10), (9, 11), (9, 12), (9, 13), (9, 14), (9, 15),
            (16, 17), (16, 18), (16, 19), (16, 20), (16, 21),
            (22, 23), (22, 24), (22, 25), (22, 26),
            (27, 28), (27, 29), (27, 30)]),
        ('linestring_l', True, [
            (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9), (1, 10),
            (11, 12), (11, 13), (11, 14), (11, 15), (11, 16), (11, 17), (11, 18), (11, 19),
            (20, 21), (20, 22), (20, 23), (20, 24), (20, 25), (20, 26), (20, 27),
            (28, 29), (28, 30), (28, 31), (28, 32), (28, 33), (28, 34),
            (35, 36), (35, 37), (35, 38), (35, 39), (35, 40)]),
        ('linestring_l', False, [
            (41, 42),
            (47, 50),
            (44, 45), (44, 46),
            (51, 52), (51, 53), (51, 54), (51, 55),
            (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9), (1, 10),
            (11, 12), (11, 13), (11, 14), (11, 15), (11, 16), (11, 17), (11, 18), (11, 19),
            (20, 21), (20, 22), (20, 23), (20, 24), (20, 25), (20, 26), (20, 27),
            (28, 29), (28, 30), (28, 31), (28, 32), (28, 33), (28, 34),
            (35, 36), (35, 37), (35, 38), (35, 39), (35, 40)]),
        ('multilinestring_ml', True, [
            (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9), (1, 10),
            (11, 12), (11, 13), (11, 14), (11, 15), (11, 16), (11, 17), (11, 18), (11, 19),
            (20, 21), (20, 22), (20, 23), (20, 24), (20, 25), (20, 26), (20, 27),
            (28, 29), (28, 30), (28, 31), (28, 32), (28, 33), (28, 34),
            (35, 36), (35, 37), (35, 38), (35, 39), (35, 40)]),
        ('multilinestring_ml', False, [
            (43, 46),
            (47, 48), (47, 49), (47, 50), (47, 51),
            (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9),
            (1, 10), (1, 11), (1, 12), (1, 13), (1, 14), (1, 15), (1, 16),
            (1, 17), (1, 18), (1, 19), (1, 20), (1, 21), (1, 22), (1, 23),
            (1, 24), (1, 25), (1, 26), (1, 27), (1, 28), (1, 29), (1, 30),
            (1, 31), (1, 32), (1, 33), (1, 34), (1, 35), (1, 36), (1, 37),
            (1, 38), (1, 39), (1, 40)]),
        ('polygon_a', True, [
            (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7),
            (8, 9), (8, 10), (8, 11)]),
        ('polygon_a', False, [
            (18, 19), (18, 20), (18, 21), (18, 22), (18, 23), (18, 24), (18, 25), (18, 26), (18, 27),
            (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9), (1, 10), (1, 11)]),
        ('multipolygon_ma', True, [
            (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7),
            (8, 9), (8, 10), (8, 11),
            (33, 34), (33, 35)]),
        ('multipolygon_ma', False, [
            (18, 19), (18, 20), (18, 21), (18, 22), (18, 23), (18, 24), (18, 25), (18, 26), (18, 27),
            (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9), (1, 10), (1, 11),
            (33, 34), (33, 35)]),
    ])
    def test_2d(self, identical, mem_gpkg, fc_name, include, expected):
        """
        Test find identical
        """
        source = identical[fc_name]
        target = Table(mem_gpkg, name='repeats')
        find_identical(source, target, fields=[REASON], include_geometry=include)
        cursor = target.select([ORIG_FID, REPEAT_FID])
        assert cursor.fetchall() == expected
    # End test_2d method

    @mark.parametrize('include, expected', [
        (True, 0),
        (False, 373),
    ])
    def test_multiple_columns(self, ntdb_zm_small, mem_gpkg, include, expected):
        """
        Test multiple fields
        """
        source = ntdb_zm_small['hydro_zm_a']
        target = Table(mem_gpkg, name='repeats')
        names = 'PART_ID', 'ENTITY', 'ENTITY_NAME', 'VALDATE', 'CODE'
        find_identical(source, target, fields=names, include_geometry=include)
        assert len(target) == expected
    # End test_multiple_columns method

    @mark.parametrize('include, expected', [
        (True, 0),
        (False, 231),
    ])
    def test_extent(self, ntdb_zm_small, mem_gpkg, include, expected):
        """
        Test extent
        """
        source = ntdb_zm_small['hydro_zm_a']
        target = Table(mem_gpkg, name='repeats')
        names = 'PART_ID', 'ENTITY', 'ENTITY_NAME', 'VALDATE', 'CODE'
        with Swap(Setting.EXTENT, Extent.from_bounds(-114.5, 51., -114.25, 51.25, crs=CRS(4326))):
            find_identical(source, target, fields=names, include_geometry=include)
        assert len(target) == expected
    # End test_extent method
# End TestFindIdentical class


if __name__ == '__main__':  # pragma: no cover
    pass
