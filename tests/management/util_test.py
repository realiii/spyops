# -*- coding: utf-8 -*-
"""
Util Tests
"""


from numpy import array
from pyproj import CRS
from pytest import approx, mark

from spyops.management.util import (
    _interpolate_coordinates, _build_planar_lines, _build_geodesic_lines)


pytestmark = [mark.management]


@mark.parametrize('point_count, expected', [
    (0, [(0, 0), (10, 10)]),
    (4, [(0, 0), (2, 2), (4, 4), (6, 6), (8, 8), (10, 10)]),
])
def test_interpolate_coordinates(point_count, expected):
    """
    Test interpolate coordinates
    """
    values = array([0, 0, 10, 10], dtype=float)
    results = _interpolate_coordinates(point_count, values)
    assert approx(results, abs=0.001) == expected
# End test_interpolate_coordinates function


def test_build_planar_lines():
    """
    Test build planar lines
    """
    coords = array([[0, 1, 2, 3], [10, 20, 30, 40]], dtype=float)
    lines = _build_planar_lines(coords, srs_id=4326, point_count=0)
    assert len(lines) == 2
    assert approx(lines[0].coordinates, abs=0.001) == [(0, 1), (2, 3)]
    assert approx(lines[1].coordinates, abs=0.001) == [(10, 20), (30, 40)]

    coords = array([[0, 0, 2, 2], [10, 10, 30, 30]], dtype=float)
    lines = _build_planar_lines(coords, srs_id=4326, point_count=1)
    assert len(lines) == 2
    assert approx(lines[0].coordinates, abs=0.001) == [(0, 0), (1, 1), (2, 2)]
    assert approx(lines[1].coordinates, abs=0.001) == [(10, 10), (20, 20), (30, 30)]
# End test_build_planar_lines function


def test_build_geodesic_lines_geographic():
    """
    Test build geodesic lines using geographic coordinates
    """
    coords = array([
        (-114.25740219999994, 51.16868930000004, -114.2575086, 51.16516610000008),
        (-114.25738169999994, 51.11641940000004, -114.25731939999997, 51.10581280000008),
        (-114.11748209999996, 51.04547510000003, -114.11749349999997, 51.04378530000008),
        (-114.25722139999999, 51.089453700000035, -114.18072199999995, 51.05874040000003),
        (-114.22939279999997, 51.01602360000004, -114.15760829999999, 51.00428620000008),
        (-114.25767769999999, 51.17586780000005, -114.25740219999994, 51.16868930000004),
        (-114.28066419999999, 51.098732400000074, -114.25722139999999, 51.089453700000035)],
        dtype=float)
    code = 4617
    lines = _build_geodesic_lines(
        coords, srs_id=code, point_count=0, crs=CRS(code))
    assert len(lines) == 7
    assert approx([line.coordinates[0][0] for line in lines], abs=0.000001) == coords[:, 0]
# End test_build_geodesic_lines_geographic function


def test_build_geodesic_lines_projected():
    """
    Test build geodesic lines using projected coordinates
    """
    coords = array([
        (51968.09530554187, 5666354.656224861, 51964.61593316551, 5665962.932202779),
        (52028.263816569866, 5660544.216479136, 52044.5357327528, 5659365.235504757),
        (61910.87852720911, 5652766.279672928, 61912.33260204084, 5652578.427768142),
        (52069.74367874031, 5657546.834572435, 57463.12108769253, 5654189.596676913),
        (54103.37252877549, 5649404.449669628, 59151.58480278234, 5648154.8174714735),
        (51940.789965290365, 5667152.442064336, 51968.09530554187, 5666354.656224861),
        (50418.553138803276, 5658561.973054729, 52069.74367874031, 5657546.834572435)],
        dtype=float)
    xs = coords[:, 0].copy()
    code = 102179
    lines = _build_geodesic_lines(
        coords, srs_id=code, point_count=0, crs=CRS(f'ESRI:{code}'))
    assert len(lines) == 7
    assert approx([line.coordinates[0][0] for line in lines], abs=0.001) == xs
# End test_build_geodesic_lines_projected function


if __name__ == '__main__':  # pragma: no cover
    pass
