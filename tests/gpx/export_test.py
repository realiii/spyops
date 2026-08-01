# -*- coding: utf-8 -*-
"""
Test GPS Exchange Export
"""


from datetime import date, datetime, time, timezone
from math import nan
from xml.etree.ElementTree import tostring

from pytest import mark

from spyops.gpx.export import (
    Date, Description, Elevation, GPX, Name,
    Segment, Track, TrackPoint, Waypoint)


pytestmark = [mark.conversion, mark.gps]


@mark.parametrize('value, expected', [
    ('', b'<name />'),
    (None, b'<name />'),
    ('asdf', b'<name>asdf</name>'),
])
def test_name(value, expected):
    """
    Test name
    """
    name = Name(value)
    assert tostring(name) == expected
# End test_name function


@mark.parametrize('value, expected', [
    ('', b'<desc />'),
    (None, b'<desc />'),
    ('asdf', b'<desc>asdf</desc>'),
])
def test_description(value, expected):
    """
    Test description
    """
    description = Description(value)
    assert tostring(description) == expected
# End test_description function


@mark.parametrize('value, expected', [
    (123, b'<ele>123</ele>'),
    (123., b'<ele>123.0</ele>'),
    (-123., b'<ele>-123.0</ele>'),
    (0, b'<ele>0</ele>'),
    ('123.456', b'<ele>123.456</ele>'),
])
def test_elevation(value, expected):
    """
    Test elevation
    """
    elevation = Elevation(value)
    assert tostring(elevation) == expected
# End test_elevation function


@mark.parametrize('value, expected', [
    (datetime(2020, 1, 2, 3, 4, 5, tzinfo=timezone.utc), b'<time>2020-01-02T03:04:05.000Z</time>'),
    (date(2025, 10, 20), b'<time>2025-10-20T05:00:00.000Z</time>'),
    (time(6, 7, 8, tzinfo=timezone.utc), b'<time>1900-01-01T06:07:08.000Z</time>'),
])
def test_date(value, expected):
    """
    Test date
    """
    dt = Date(value)
    assert tostring(dt) == expected
# End test_date function


@mark.parametrize('point, time_, expected', [
    ((0.123, 1.234, nan), None,
     b'<trkpt lon="0.123" lat="1.234" />'),
    ((0.123, 1.234, 2.345), None,
     b'<trkpt lon="0.123" lat="1.234"><ele>2.345</ele></trkpt>'),
    ((0.123, 1.234, 2.345), datetime(2020, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
     b'<trkpt lon="0.123" lat="1.234"><ele>2.345</ele><time>2020-01-02T03:04:05.000Z</time></trkpt>'),
])
def test_trackpoint(point, time_, expected):
    """
    Test TrackPoint
    """
    pt = TrackPoint.from_data(point, time_=time_)
    assert tostring(pt) == expected
# End test_trackpoint function


@mark.parametrize('point, time_, name, desc, expected', [
    ((0.123, 1.234, nan), None, None, None,
     b'<wpt lon="0.123" lat="1.234" />'),
    ((0.123, 1.234, 2.345), None, None, None,
     b'<wpt lon="0.123" lat="1.234"><ele>2.345</ele></wpt>'),
    ((0.123, 1.234, 2.345), datetime(2020, 1, 2, 3, 4, 5, tzinfo=timezone.utc), None, None,
     b'<wpt lon="0.123" lat="1.234"><ele>2.345</ele><time>2020-01-02T03:04:05.000Z</time></wpt>'),
    ((0.123, 1.234, 2.345), datetime(2020, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
     'abcdef', 'lmno', b'<wpt lon="0.123" lat="1.234"><ele>2.345</ele><time>2020-01-02T03:04:05.000Z</time><name>abcdef</name><desc>lmno</desc></wpt>'),
])
def test_waypoint(point, time_, name, desc, expected):
    """
    Test Waypoint
    """
    pt = Waypoint.from_data(point, time_=time_, name=name, description=desc)
    assert tostring(pt) == expected
# End test_waypoint function


@mark.parametrize('points, expected', [
    ([], b'<trkseg />'),
    ([(0.123, 1.234, 5)],
     b'<trkseg><trkpt lon="0.123" lat="1.234"><ele>5</ele></trkpt></trkseg>'),
    ([(0.123, 1.234, 6), (0.234, 2.345, 7)],
     b'<trkseg><trkpt lon="0.123" lat="1.234"><ele>6</ele></trkpt><trkpt lon="0.234" lat="2.345"><ele>7</ele></trkpt></trkseg>'),
])
def test_segment(points, expected):
    """
    Test Segment
    """
    if points:
        points = [TrackPoint.from_data(point, time_=None)
                  for point in points]
    seg = Segment(points)
    assert tostring(seg) == expected
# End test_segment function


@mark.parametrize('points, name, desc, expected', [
    ([(0.123, 1.234, 5)], None, None,
     b'<trk><trkseg><trkpt lon="0.123" lat="1.234"><ele>5</ele><time>2020-01-02T03:04:05.000Z</time></trkpt></trkseg></trk>'),
    ([(0.123, 1.234, 6), (0.234, 2.345, 7)], 'asdf', 'lmno',
     b'<trk><name>asdf</name><desc>lmno</desc><trkseg><trkpt lon="0.123" lat="1.234"><ele>6</ele><time>2020-01-02T03:04:05.000Z</time></trkpt><trkpt lon="0.234" lat="2.345"><ele>7</ele><time>2020-01-02T03:04:05.000Z</time></trkpt></trkseg></trk>'),
])
def test_track(points, name, desc, expected):
    """
    Test Track
    """
    if points:
        time_ = datetime(2020, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
        points = [TrackPoint.from_data(point, time_=time_)
                  for point in points]
    trk = Track.from_data(Segment(points), name=name, description=desc)
    assert tostring(trk) == expected
# End test_track function


def test_gpx():
    """
    Test GPX
    """
    gpx = GPX([], [])
    assert tostring(gpx) == b'<gpx xmlns="http://www.topografix.com/GPX/1/1" xalan="http://xml.apache.org/xalan" xsi="http://www.w3.org/2001/XMLSchema-instance" creator="spyops" version="1.1" />'
# End test_gpx function


if __name__ == '__main__':  # pragma: no cover
    pass
