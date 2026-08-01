# -*- coding: utf-8 -*-
"""
GPS Exchange Format Parse
"""


from datetime import datetime
from functools import cached_property
from math import nan
from pathlib import Path
from re import compile as recompile
from tempfile import mkdtemp
from typing import Callable
from xml.etree.ElementTree import Element, ParseError, iterparse

from shapely import LineString as ShapelyLineString, Point as ShapelyPoint

from spyops.shared.keywords import LAT_KEY, LON_KEY
from spyops.shared.hint import NUMBER
from spyops.shared.util import safe_float


MATCH_SEVEN_PLACES: Callable = recompile(r'\.\d{7}Z').search


def _update_element_tag(source: Path):
    """
    Update element tag
    """
    try:
        tree = iterparse(source)
        for _, el in tree:
            _, _, el.tag = el.tag.rpartition('}')
    except ParseError:
        return False, None
    return True, tree
# End _update_element_tag function


def _to_datetime(text: str) -> datetime | None:
    """
    Convert Zulu or ISO representation of Time from String to Datetime
    """
    try:
        return datetime.strptime(text, '%Y-%m-%dT%H:%M:%SZ')
    except TypeError:  # pragma: no cover
        return None
    except ValueError:
        pass
    micro: str = '%Y-%m-%dT%H:%M:%S.%fZ'
    try:
        return datetime.strptime(text, micro)
    except ValueError:
        pass
    if MATCH_SEVEN_PLACES(text):
        text = f'{text[:-2]}Z'
    try:
        return datetime.strptime(text, micro)
    except ValueError:
        pass
    try:
        return datetime.fromisoformat(text)
    except ValueError:  # pragma: no cover
        return None
# End _to_datetime function


def get_root(path: Path) -> Element:
    """
    Get root from the XML file and strip URLs from tags.
    """
    msg = f'Unable to parse {path}'
    success, tree = _update_element_tag(path)
    if not success:
        try:
            # NOTE strip leading whitespace to avoid parse error
            output_path = Path().joinpath(mkdtemp(), path.name)
            with path.open() as fin:
                with output_path.open('w') as fout:
                    fout.write(fin.read().strip())
            success, tree = _update_element_tag(output_path)
        except UnicodeDecodeError:
            success = False
        if not success:
            raise IOError(msg)
    if (root := tree.root) is None:
        raise IOError(msg)
    return root
# End get_root function


class BaseParse:
    """
    Base Parse
    """
    def __init__(self, element: Element) -> None:
        """
        Initialize the BaseParse class
        """
        super().__init__()
        self._element: Element = element
    # End init built-in

    def _select_string_value(self, key: str) -> str | None:
        """
        Select String Value
        """
        if (value := self._element.find(f'./{key}')) is None:
            return None
        if not (value := value.text):
            return None
        if not (value := value.strip()):
            return None
        return value
    # End _select_string_value method

    @property
    def name(self) -> str | None:
        """
        Name
        """
        return self._select_string_value('name')
    # End name property

    @property
    def description(self) -> str | None:
        """
        Description
        """
        return self._select_string_value('desc')
    # End description property

    @property
    def type(self) -> str | None:
        """
        Type
        """
        return self._select_string_value('type')
    # End type property
# End BaseParse class


class Point(BaseParse):
    """
    Point
    """
    @property
    def geometry(self) -> ShapelyPoint:
        """
        Geometry
        """
        try:
            x = safe_float(self._element.attrib[LON_KEY])
            y = safe_float(self._element.attrib[LAT_KEY])
        except KeyError:
            x = y = None
        if x is None or y is None:
            x = y = nan
        if (z := self.elevation) is None:
            z = nan
        return ShapelyPoint(x, y, z)
    # End geometry property

    @property
    def comment(self) -> str | None:
        """
        Comment
        """
        return self._select_string_value('cmt')
    # End comment property

    @property
    def symbol(self) -> str | None:
        """
        Symbol
        """
        return self._select_string_value('sym')
    # End symbol property

    @cached_property
    def elevation(self) -> NUMBER | None:
        """
        Elevation
        """
        if not (value := self._select_string_value('ele')):
            return None
        return float(value)
    # End elevation property

    @property
    def dt(self) -> datetime | None:
        """
        Date Time
        """
        if not (value := self._select_string_value('time')):
            return None
        return _to_datetime(value)
    # End dt property

    def as_record(self) -> tuple:
        """
        As Record
        """
        return (self.geometry, self.name, self.description, self.type,
                self.comment, self.symbol, self.elevation, self.dt)
    # End as_record method
# End Point class


class Line(BaseParse):
    """
    Line
    """
    @property
    def geometry(self) -> list[ShapelyLineString]:
        """
        Geometry
        """
        segments = []
        for segment in self._element.findall('./trkseg'):
            points = segment.findall('./trkpt')
            if len(points) < 2:
                continue
            geoms = [Point(pt).geometry for pt in points]
            geoms = [geom for geom in geoms if not geom.is_empty]
            if len(geoms) < 2:
                continue
            segments.append(ShapelyLineString(geoms))
        return segments
    # End geometry property

    def as_record(self) -> tuple:
        """
        As Record
        """
        return self.geometry, self.name, self.description, self.type
    # End as_record method
# End Line class


def get_waypoints(root: Element) -> list['Point']:
    """
    Get Waypoints
    """
    points = root.findall('./wpt')
    return [Point(pt) for pt in points]
# End get_waypoints function


def get_trackpoints(root: Element) -> list['Point']:
    """
    Get Track Points
    """
    points = []
    for track in root.findall('./trk'):
        for segment in track.findall('./trkseg'):
            points.extend([Point(pt) for pt in segment.findall('./trkpt')])
    return points
# End get_trackpoints function


def get_tracks(root: Element) -> list['Line']:
    """
    Get Tracks
    """
    return [Line(track) for track in root.findall('./trk')]
# End get_tracks function


if __name__ == '__main__':  # pragma: no cover
    pass
