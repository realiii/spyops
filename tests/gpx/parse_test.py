# -*- coding: utf-8 -*-
"""
Test GPS Exchange Parse
"""


from datetime import datetime
from math import nan
from xml.etree.ElementTree import Element

from pytest import approx, mark

from spyops.gpx.parse import (
    get_root, get_trackpoints, get_tracks, get_waypoints)


pytestmark = [mark.conversion, mark.gps]


@mark.parametrize('name', [
    'line_attr.gpx',
    'line_sans_attr.gpx',
    'multiline_attr.gpx',
    'multiline_attr_dt.gpx',
    'multiline_sans_attr.gpx',
    'multipoint_attr.gpx',
    'multipoint_sans_attr.gpx',
    'point_2d_sans_attr.gpx',
    'point_all_attr.gpx',
    'point_attr_geom_elev.gpx',
    'point_sans_attr.gpx',
])
def test_get_root(gpx_path, name):
    """
    test get URL stripped root
    """
    path = gpx_path / name
    assert path.is_file()
    assert isinstance(get_root(path), Element)
# End test_get_root function


@mark.parametrize('name, count', [
    ('line_attr.gpx', 0),
    ('line_sans_attr.gpx', 0),
    ('multiline_attr.gpx', 0),
    ('multiline_attr_dt.gpx', 0),
    ('multiline_sans_attr.gpx', 0),
    ('multipoint_attr.gpx', 142),
    ('multipoint_sans_attr.gpx', 142),
    ('point_2d_sans_attr.gpx', 3912),
    ('point_all_attr.gpx', 3912),
    ('point_attr_geom_elev.gpx', 3912),
    ('point_sans_attr.gpx', 3912),
])
def test_get_waypoints(gpx_path, name, count):
    """
    Test get waypoints
    """
    path = gpx_path / name
    assert path.is_file()
    root = get_root(path)
    assert len(get_waypoints(root)) == count
# End test_get_waypoints function


@mark.parametrize('name, coords, record', [
    ('multipoint_attr.gpx', (-114.4926, 51.0872, 1224.7774),
     ['Named feature', '1977', None, None, None, 1224.7774999999965, None]),
    ('multipoint_sans_attr.gpx', (-114.4926, 51.0872, nan),
     [None, None, None, None, None, None, None]),
    ('point_2d_sans_attr.gpx', (-114.0575, 51.0373, nan),
     [None, None, None, None, None, None, None]),
    ('point_all_attr.gpx', (-114.0575, 51.0373, 1045.7905),
     ['Historic site/Point of interest', 'Historic site/Point of interest',
      None, None, None, 1045.790599999993, datetime(2026, 6, 6, 17, 4, 8)]),
    ('point_attr_geom_elev.gpx', (-114.0575, 51.0373, 1045.7905),
     ['Historic site/Point of interest', 'Historic site/Point of interest',
      None, None, None, 1045.790599999993, datetime(2026, 6, 6, 17, 4, 8)]),
    ('point_sans_attr.gpx', (-114.0575, 51.0373, nan),
     [None, None, None, None, None, None, None]),
])
def test_waypoint_record(gpx_path, name, coords, record):
    """
    Test Waypoint Record
    """
    path = gpx_path / name
    assert path.is_file()
    root = get_root(path)
    point, *_ = get_waypoints(root)
    geom, *values = point.as_record()
    assert approx((geom.x, geom.y, geom.z), abs=0.001, nan_ok=True) == coords
    assert values == record
# End test_waypoint_record function


@mark.parametrize('name, count', [
    ('line_attr.gpx', 1744),
    ('line_sans_attr.gpx', 872),
    ('multiline_attr.gpx', 2255),
    ('multiline_attr_dt.gpx', 2255),
    ('multiline_sans_attr.gpx', 872),
    ('multipoint_attr.gpx', 0),
    ('multipoint_sans_attr.gpx', 0),
    ('point_2d_sans_attr.gpx', 0),
    ('point_all_attr.gpx', 0),
    ('point_attr_geom_elev.gpx', 0),
    ('point_sans_attr.gpx', 0),
])
def test_get_trackpoints(gpx_path, name, count):
    """
    Test get trackpoints
    """
    path = gpx_path / name
    assert path.is_file()
    root = get_root(path)
    assert len(get_trackpoints(root)) == count
# End test_get_trackpoints function


@mark.parametrize('name, coords, record', [
    ('line_attr.gpx', (-114.4923, 51.2202, 1253.8251),
     [None, None, None, None, None, 1253.8251000000018, None]),
    ('line_sans_attr.gpx', (-114.4923, 51.2202, nan),
     [None, None, None, None, None, None, None]),
    ('multiline_attr.gpx', (-114.2564, 51.1686, 1284.5117),
     [None, None, None, None, None, 1284.5117000000027,
      datetime(2026, 6, 12, 8, 48)]),
    ('multiline_attr_dt.gpx', (-114.2564, 51.1686, 1284.5117),
     [None, None, None, None, None, 1284.5117000000027,
      datetime(2026, 6, 12, 8, 48)]),
    ('multiline_sans_attr.gpx', (-114.4923, 51.2202, nan),
     [None, None, None, None, None, None, None]),
])
def test_trackpoint_record(gpx_path, name, coords, record):
    """
    Test Track Point Record
    """
    path = gpx_path / name
    assert path.is_file()
    root = get_root(path)
    point, *_ = get_trackpoints(root)
    geom, *values = point.as_record()
    assert approx((geom.x, geom.y, geom.z), abs=0.001, nan_ok=True) == coords
    assert values == record
# End test_trackpoint_record function


@mark.parametrize('name, count', [
    ('line_attr.gpx', 4),
    ('line_sans_attr.gpx', 4),
    ('multiline_attr.gpx', 66),
    ('multiline_attr_dt.gpx', 66),
    ('multiline_sans_attr.gpx', 4),
    ('multipoint_attr.gpx', 0),
    ('multipoint_sans_attr.gpx', 0),
    ('point_2d_sans_attr.gpx', 0),
    ('point_all_attr.gpx', 0),
    ('point_attr_geom_elev.gpx', 0),
    ('point_sans_attr.gpx', 0),
])
def test_get_tracks(gpx_path, name, count):
    """
    Test get tracks
    """
    path = gpx_path / name
    assert path.is_file()
    root = get_root(path)
    tracks = get_tracks(root)
    assert len(tracks) == count
# End test_get_tracks function


@mark.parametrize('name, record', [
    ('line_attr.gpx', ['Pipeline', 'Multiuse, underground', None]),
    ('line_sans_attr.gpx', [None, None, None]),
    ('multiline_attr.gpx', ['Power transmission line', 'Overhead', None]),
    ('multiline_attr_dt.gpx', ['Power transmission line', 'Overhead', None]),
    ('multiline_sans_attr.gpx', [None, None, None]),
])
def test_track_record(gpx_path, name, record):
    """
    Test track record
    """
    path = gpx_path / name
    assert path.is_file()
    root = get_root(path)
    track, *_ = get_tracks(root)
    lines, *values = track.as_record()
    assert len(lines) == 1
    line, *_ = lines
    assert line.is_valid
    assert values == record
# End test_track_record function


if __name__ == '__main__':  # pragma: no cover
    pass
