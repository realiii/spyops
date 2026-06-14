# -*- coding: utf-8 -*-
"""
GPS Exchange Format Export
"""


from datetime import date, datetime, time, timezone
from typing import Any, Self
from xml.etree.ElementTree import Element

from numpy import isfinite, ndarray

from spyops.shared.constant import LAT, LON, SPYOPS
from spyops.shared.hint import NUMBER


class BaseGPXElement(Element):
    """
    Base GPX Element
    """
    def __init__(self, value: Any = None,
                 attributes: dict | None = None) -> None:
        """
        Initialize the BaseGPXElement class
        """
        attributes = attributes or {}
        if self.tag:
            tag = self.tag
        else:
            tag = self.__class__.__name__
        super().__init__(tag, attributes)
        if value is not None:
            self.text = f'{value}'
    # End init built-in
# End BaseGPXElement class


class Name(BaseGPXElement):
    """
    Name
    """
    tag: str = 'name'

    def __init__(self, value: str) -> None:
        """
        Initialize the Name class
        """
        super().__init__(value)
    # End init built-in
# End Name class


class Description(BaseGPXElement):
    """
    Description
    """
    tag: str = 'desc'

    def __init__(self, value: str) -> None:
        """
        Initialize the Description class
        """
        super().__init__(value)
    # End init built-in
# End Description class


class Elevation(BaseGPXElement):
    """
    Elevation
    """
    tag: str = 'ele'

    def __init__(self, value: NUMBER) -> None:
        """
        Initialize the Elevation class
        """
        super().__init__(value)
    # End init built-in
# End Elevation class


class Date(BaseGPXElement):
    """
    Date
    """
    tag: str = 'time'

    def __init__(self, value: datetime) -> None:
        """
        Initialize the Date class
        """
        if isinstance(value, datetime):
            pass
        elif isinstance(value, time):
            value = datetime.combine(date(1900, 1, 1), value)
        elif isinstance(value, date):
            value = datetime.combine(value, time())
        value = value.astimezone(timezone.utc)
        super().__init__(f"{value.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]}Z")
    # End init built-in
# End Date class


class TrackPoint(BaseGPXElement):
    """
    Track Point
    """
    tag: str = 'trkpt'

    def __init__(self, lon: NUMBER, lat: NUMBER,
                 elevation: Elevation | None = None,
                 dt: Date | None = None) -> None:
        """
        Initialize the TrackPoint class
        """
        super().__init__(attributes={LON: f'{lon}', LAT: f'{lat}'})
        if elevation is not None:
            self.append(elevation)
        if dt is not None:
            self.append(dt)
    # End init built-in

    @classmethod
    def from_data(cls, point: 'ndarray', time_: datetime | None) -> Self:
        """
        From Data
        """
        x, y, z = point
        if isfinite(z):
            elevation = Elevation(z)
        else:
            elevation = None
        if isinstance(time_, (datetime, date, time)):
            dt = Date(time_)
        else:
            dt = None
        return cls(lon=x, lat=y, elevation=elevation, dt=dt)
    # End from_data method
# End TrackPoint class


class Waypoint(BaseGPXElement):
    """
    Waypoint
    """
    tag: str = 'wpt'

    def __init__(self, lon: NUMBER, lat: NUMBER,
                 elevation: Elevation | None = None,
                 dt: Date | None = None,
                 name: Name | None = None,
                 description: Description | None = None) -> None:
        """
        Initialize the Waypoint class
        """
        super().__init__(attributes={LON: f'{lon}', LAT: f'{lat}'})
        if elevation is not None:
            self.append(elevation)
        if dt is not None:
            self.append(dt)
        if name is not None:
            self.append(name)
        if description is not None:
            self.append(description)
    # End init built-in

    @classmethod
    def from_data(cls, point: tuple[NUMBER, NUMBER, NUMBER],
                  time_: datetime | None, name: str | None,
                  description: str | None) -> Self:
        """
        From Data
        """
        x, y, z = point
        if isfinite(z):
            elevation = Elevation(z)
        else:
            elevation = None
        if isinstance(time_, (datetime, date, time)):
            dt = Date(time_)
        else:
            dt = None
        if name:
            name = Name(name)
        else:
            name = None
        if description:
            description = Description(description)
        else:
            description = None
        return cls(lon=x, lat=y, elevation=elevation, dt=dt,
                   name=name, description=description)
    # End from_data method
# End Waypoint class


class Segment(BaseGPXElement):
    """
    Segment
    """
    tag: str = 'trkseg'

    def __init__(self, points: list[TrackPoint]) -> None:
        """
        Initialize the Segment class
        """
        super().__init__()
        self.extend(points)
    # End init built-in
# End Segment class


class Track(BaseGPXElement):
    """
    Track
    """
    tag: str = 'trk'

    def __init__(self, segment: Segment, name: Name | None,
                 description: Description | None) -> None:
        """
        Initialize the Track class
        """
        super().__init__()
        if name is not None:
            self.append(name)
        if description is not None:
            self.append(description)
        self.append(segment)
    # End init built-in

    @classmethod
    def from_data(cls, points: list[TrackPoint], name: str | None,
                  description: str | None) -> Self:
        """
        From Data
        """
        if name:
            name = Name(name)
        else:
            name = None
        if description:
            description = Description(description)
        else:
            description = None
        return cls(segment=Segment(points), name=name, description=description)
    # End from_data method
# End Track class


class GPX(BaseGPXElement):
    """
    GPS Exchange Format
    """
    tag: str = 'gpx'

    def __init__(self, tracks: list[Track], waypoints: list[Waypoint]) -> None:
        """
        Initialize the GPX class
        """
        super().__init__(attributes={
            'xmlns': 'http://www.topografix.com/GPX/1/1',
            'xalan': 'http://xml.apache.org/xalan',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'creator': SPYOPS,
            'version': '1.1',
        })
        self.extend(tracks)
        self.extend(waypoints)
    # End init built-in
# End GPX class


if __name__ == '__main__':  # pragma: no cover
    pass
