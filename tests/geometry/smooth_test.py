# -*- coding: utf-8 -*-
"""
Smooth Tests
"""


from pytest import mark, approx
from shapely import LineString, MultiLineString
from shapely.io import from_wkt

from spyops.geometry.smooth import smooth_bezier, smooth_paek


pytestmark = [mark.geometry]


class TestSmoothPAEK:
    """
    Test Smooth PAEK
    """
    @mark.parametrize('line, expected', [
        (LineString([(0, 0), (1, 2), (2, 1), (3, 3), (4, 0)]),
         [[0.0, 0.0], [1.019, 1.888], [1.982, 1.123], [3.001, 2.968], [4.0, 0.0]]),
        (LineString([(0, 0, 0), (1, 2, 10), (2, 1, 5), (3, 3, 12), (4, 0, 0)]),
         [[0.0, 0.0, 0.0], [1.019, 1.888, 9.480], [1.982, 1.123, 5.548],
          [3.001, 2.968, 11.879], [4.0, 0.0, 0.0]]),
    ])
    def test_smooth_line(self, line, expected):
        """
        Test Smooth Polyline PAEK LineString
        """
        smoothed = smooth_paek(line, tolerance=1.5)
        assert isinstance(smoothed, LineString)
        assert smoothed.has_z == line.has_z
        assert len(smoothed.coords) == len(line.coords)
        assert smoothed.coords[0] == line.coords[0]
        assert smoothed.coords[-1] == line.coords[-1]
        assert approx(smoothed.coords, abs=0.001) == expected
        assert smoothed != line
    # End test_smooth_line function

    @mark.zm
    @mark.parametrize('line, expected', [
        ('LineString M (0 0 0, 1 2 10, 2 1 5, 3 3 12, 4 0 0)',
         [[0.0, 0.0, 0.0], [1.019, 1.888, 9.480], [1.982, 1.123, 5.548], 
          [3.001, 2.968, 11.879], [4.0, 0.0, 0.0]]),
        ('LineString (0 0 0 0, 1 2 10 123, 2 1 5 456, 3 3 12 789, 4 0 0 1011)',
         [[0.0, 0.0, 0.0, 0.0], [1.019, 1.888, 9.480, 133.156],
          [1.982, 1.123, 5.548, 447.788], [3.001, 2.968, 11.879, 788.766],
          [4.0, 0.0, 0.0, 1011.0]]),
    ])
    def test_smooth_line_zm(self, line, expected):
        """
        Test Smooth Polyline PAEK LineString with measures
        """
        line = from_wkt(line)
        smoothed = smooth_paek(line, tolerance=1.5)
        assert isinstance(smoothed, LineString)
        assert smoothed.has_z == line.has_z
        assert smoothed.has_m
        assert len(smoothed.coords) == len(line.coords)
        assert smoothed.coords[0] == line.coords[0]
        assert smoothed.coords[-1] == line.coords[-1]
        assert approx(smoothed.coords, abs=0.001) == expected
        assert smoothed != line
    # End test_smooth_line_zm function

    def test_smooth_multiline(self):
        """
        Test Smooth Polyline PAEK MultiLineString
        """
        multiline = MultiLineString([
            [(0, 0), (1, 2), (2, 1), (3, 0)],
            [(10, 0), (11, 3), (12, 1), (13, 0)],
        ])
        expected = (
            [[0.0, 0.0], [1.006, 1.961], [1.990, 1.061], [3.0, 0.0]],
            [[10.0, 0.0], [10.998, 2.987], [12.002, 1.024], [13.0, 0.0]],
        )
        smoothed = smooth_paek(multiline, tolerance=1.5)
        assert isinstance(smoothed, MultiLineString)
        assert len(smoothed.geoms) == len(multiline.geoms)
        for original, result, coords in zip(multiline.geoms, smoothed.geoms, expected):
            assert len(result.coords) == len(original.coords)
            assert result.coords[0] == original.coords[0]
            assert result.coords[-1] == original.coords[-1]
            assert approx(result.coords, abs=0.001) == coords
            assert result != original
    # End test_smooth_multiline function
# End TestSmoothPAEK class


class TestSmoothBezier:
    """
    Test Smooth Bezier
    """
    @mark.parametrize('line, count, expected', [
        (LineString([(0, 0), (5, 10), (10, 0), (15, 5)]), 0,
         [[0.0, 0.0], [5.0, 10.0], [10.0, 0.0], [15.0, 5.0]]),
        (LineString([(0, 0), (5, 10), (10, 0), (15, 5)]), 3,
         [[0.0, 0.0], [1.25, 2.968], [2.5, 6.25], [3.75, 8.906], [5.0, 10.0],
          [6.166, 8.392], [7.277, 4.878], [8.499, 1.426], [10.0, 0.0],
          [11.149, 0.633], [12.411, 1.951], [13.716, 3.544], [15.0, 5.0]]),
        (LineString([(0, 0), (5, 10), (10, 0), (15, 5)]), 8,
         [[0.0, 0.0], [0.555, 1.220], [1.111, 2.606], [1.666, 4.074],
          [2.222, 5.541], [2.777, 6.927], [3.333, 8.148], [3.888, 9.122],
          [4.444, 9.766], [5.0, 10.0], [5.536, 9.646], [6.042, 8.700],
          [6.534, 7.335], [7.026, 5.723], [7.533, 4.037], [8.069, 2.449],
          [8.649, 1.131], [9.288, 0.257], [10.0, 0.0], [10.493, 0.170],
          [11.015, 0.521], [11.561, 1.016], [12.124, 1.620], [12.699, 2.296],
          [13.280, 3.008], [13.861, 3.720], [14.436, 4.396], [15.0, 5.0]]),
        (LineString([(0, 0, 5), (5, 10, 11), (10, 0, 23), (15, 5, 29)]), 8,
         [[0.0, 0.0, 5.0], [0.555, 1.220, 5.633], [1.111, 2.606, 6.218],
          [1.666, 4.074, 6.777], [2.222, 5.541, 7.337], [2.777, 6.927, 7.921],
          [3.333, 8.148, 8.555], [3.888, 9.122, 9.263], [4.444, 9.766, 10.069],
          [5.0, 10.0, 11.0], [5.536, 9.646, 12.086], [6.042, 8.700, 13.322],
          [6.534, 7.335, 14.669], [7.026, 5.723, 16.090],
          [7.533, 4.037, 17.548], [8.069, 2.449, 19.005],
          [8.649, 1.131, 20.425], [9.288, 0.257, 21.768], [10.0, 0.0, 23.0],
          [10.493, 0.170, 23.720], [11.015, 0.521, 24.416],
          [11.561, 1.016, 25.091], [12.124, 1.620, 25.751],
          [12.699, 2.296, 26.400], [13.280, 3.008, 27.045],
          [13.861, 3.720, 27.690], [14.436, 4.396, 28.340], [15.0, 5.0, 29.0]]),
    ])
    def test_smooth(self, line, count, expected):
        """
        Test Bezier smoothing
        """
        smoothed = smooth_bezier(line, density=count)
        smoothed_coords = list(smoothed.coords)
        for coord in line.coords:
            assert coord in smoothed_coords
        assert approx(smoothed.coords, abs=0.001) == expected
    # End test_smooth function

    def test_smooth_multiline(self):
        """
        Test Bezier smoothing supports MultiLineString.
        """
        geometry = MultiLineString([
            [(0, 0), (5, 10), (10, 0)],
            [(20, 0), (25, 5), (30, 0)],
        ])
        expected = (
            [[0.0, 0.0], [1.000, 2.320], [2.0, 4.960], [3.000, 7.440],
             [4.0, 9.280], [5.0, 10.0], [6.000, 9.280], [7.0, 7.44],
             [8.0, 4.959], [9.0, 2.319], [10.0, 0.0]],
            [[20.0, 0.0], [21.000, 1.160], [22.0, 2.480], [23.0, 3.720],
             [24.0, 4.640], [25.0, 5.0], [26.000, 4.640], [27.000, 3.72],
             [28.0, 2.479], [29.0, 1.159], [30.0, 0.0]]
        )
        smoothed = smooth_bezier(geometry, density=4)
        assert len(smoothed.geoms) == 2
        for original, result, coords in zip(geometry.geoms, smoothed.geoms, expected):
            assert approx(result.coords, abs=0.001) == coords
            assert result.coords[0] == original.coords[0]
            assert result.coords[-1] == original.coords[-1]
    # End test_smooth_multiline function
# End TestSmoothBezier class


if __name__ == '__main__':  # pragma: no cover
    pass
