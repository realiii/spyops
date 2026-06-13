# -*- coding: utf-8 -*-
"""
Query Classes for conversion.gps module
"""


from abc import abstractmethod
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Type
from xml.etree.ElementTree import Element, tostring

from fudgeo.constant import COMMA_SPACE, FETCH_SIZE
from fudgeo.enumeration import ShapeType
from numpy import isfinite
from pyproj import CRS
from shapely.coordinates import get_coordinates

from spyops.crs.util import srs_from_crs
from spyops.environment import ANALYSIS_SETTINGS
from spyops.geometry.util import (
    filter_features, find_slice_indexes,
    get_geoms_iter, to_shapely)
from spyops.query.base import AbstractSourceQuery
from spyops.query.conversion.exchange import GPX, Track, TrackPoint, Waypoint
from spyops.shared.constant import EMPTY
from spyops.shared.field import get_geometry_column_name
from spyops.shared.hint import OPT_FIELD


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass, SpatialReferenceSystem
    from numpy import ndarray


class AbstractQueryFeaturesToGPX(AbstractSourceQuery):
    """
    Abstract Query Features to GPX
    """
    def __init__(self, source: 'FeatureClass', name_field: OPT_FIELD,
                 description_field: OPT_FIELD, z_field: OPT_FIELD,
                 date_field: OPT_FIELD, where_clause: str) -> None:
        """
        Initialize the AbstractQueryFeaturesToGPX class
        """
        # noinspection PyTypeChecker
        super().__init__(source, target=None, where_clause=where_clause)
        self._fields: tuple[OPT_FIELD, ...] = (
            name_field, description_field, z_field, date_field)
    # End init built-in

    @staticmethod
    def _export_to_path(path: Path, gpx: Element) -> None:
        """
        Export to Path
        """
        with path.open('wb') as fout:
            fout.write(b'<?xml version="1.0" encoding="utf-8"?>')
            fout.write(tostring(gpx, encoding='utf-8'))
    # End _export_to_path method

    def _get_attribute_select(self) -> str:
        """
        Get Attribute Select Names
        """
        names = []
        for field in self._fields:
            if field:
                names.append(field.escaped_name)
            else:
                names.append('NULL')
        return COMMA_SPACE.join(names)
    # End _get_attribute_select method

    def _build_gpx(self) -> 'GPX':
        """
        Build GPX
        """
        records = []
        with self.source.geopackage.connection as cin:
            cursor = cin.execute(self.select)
            while features := cursor.fetchmany(FETCH_SIZE):
                if not (features := filter_features(features)):
                    continue
                features, geometries = to_shapely(
                    features, transformer=self.source_transformer)
                attributes = [f[1:] for f in features]
                records.extend(self._build_records(geometries, attributes))
        return self._records_to_gpx(records)
    # End _build_gpx method

    @abstractmethod
    def _records_to_gpx(self, records: list) -> 'GPX':
        """
        Records to GPX
        """
        pass
    # End _records_to_gpx method

    @abstractmethod
    def _build_records(self, geometries: 'ndarray',
                       attributes: list[tuple]) -> list:
        """
        Build Records
        """
        pass
    # End _build_records method

    @cached_property
    def spatial_reference_system(self) -> 'SpatialReferenceSystem':
        """
        Spatial Reference System
        """
        # NOTE GPX format requires WGS84
        return srs_from_crs(CRS(4326))
    # End spatial_reference_system property

    @property
    def select(self) -> str:
        """
        Select Geometry and Optional Attribute Fields
        """
        geom_type = get_geometry_column_name(
            self.source, include_geom_type=True)
        where_clause = self._get_where_clause()
        select_names = self._get_attribute_select()
        select_names = self._concatenate(geom_type, select_names)
        if ANALYSIS_SETTINGS.extent:
            return self._make_intersection_query(
                self.source, field_names=select_names,
                where_clause=where_clause)
        return self._make_select(
            self.source, field_names=select_names, where_clause=where_clause)
    # End select property

    def export(self, path: Path) -> Path:
        """
        Build GPX format and Export to Path
        """
        gpx = self._build_gpx()
        self._export_to_path(path, gpx)
        return path
    # End export method

    @property
    def insert(self) -> str:
        """
        Overload
        """
        return EMPTY
    # End insert property
# End AbstractQueryFeaturesToGPX class


class QueryFeaturesToGPXLineString(AbstractQueryFeaturesToGPX):
    """
    Query Features to GPX Line String
    """
    def _build_records(self, geometries: 'ndarray',
                       attributes: list[tuple]) -> list['Track']:
        """
        Build Records
        """
        tracks = []
        coords, indexes = get_coordinates(
            geometries, include_z=True, return_index=True)
        ids = find_slice_indexes(indexes)
        for begin, end, attrs in zip(ids[:-1], ids[1:], attributes):
            coordinates = coords[begin:end]
            mask = isfinite(coordinates[:, 0]) & isfinite(coordinates[:, 1])
            coordinates = coordinates[mask]
            if not len(coordinates):
                continue
            name, desc, elev, time = attrs
            if elev is not None and isfinite(elev):
                coordinates[:, 2][~isfinite(coordinates[:, 2])] = elev
            points = [TrackPoint.from_data(pt, time) for pt in coordinates]
            tracks.append(Track.from_data(points, name=name, description=desc))
        return tracks
    # End _build_records method

    def _records_to_gpx(self, records: list['Track']) -> 'GPX':
        """
        Records to GPX
        """
        return GPX(tracks=records, waypoints=[])
    # End _records_to_gpx method
# End QueryFeaturesToGPXLineString class


class QueryFeaturesToGPXMultiLineString(QueryFeaturesToGPXLineString):
    """
    Query Features to GPX Multi Line String
    """
    def _build_records(self, geometries: 'ndarray',
                       attributes: list[tuple]) -> list['Track']:
        """
        Build Records
        """
        tracks = []
        for geom in geometries:
            geoms = get_geoms_iter(geom)
            # noinspection PyTypeChecker
            tracks.extend(super()._build_records(geoms, attributes))
        return tracks
    # End _build_records method
# End QueryFeaturesToGPXMultiLineString class


class QueryFeaturesToGPXPoint(AbstractQueryFeaturesToGPX):
    """
    Query Features to GPX Point
    """
    def _build_records(self, geometries: 'ndarray',
                       attributes: list[tuple]) -> list['Waypoint']:
        """
        Build Records
        """
        waypoints = []
        coordinates = get_coordinates(geometries, include_z=True)
        mask = isfinite(coordinates[:, 0]) & isfinite(coordinates[:, 1])
        for coordinates, attrs, truth in zip(coordinates, attributes, mask):
            if not truth:
                continue
            x, y, z = coordinates
            name, desc, elev, time = attrs
            if not isfinite(z) and elev is not None and isfinite(elev):
                z = elev
            waypoints.append(Waypoint.from_data(
                point=(x, y, z), time_=time, name=name, description=desc))
        return waypoints
    # End _build_records method

    def _records_to_gpx(self, records: list['Waypoint']) -> 'GPX':
        """
        Records to GPX
        """
        return GPX(tracks=[], waypoints=records)
    # End _records_to_gpx method
# End QueryFeaturesToGPXPoint class


class QueryFeaturesToGPXMultiPoint(QueryFeaturesToGPXPoint):
    """
    Query Features to GPX Multi Point
    """
    def _build_records(self, geometries: 'ndarray',
                       attributes: list[tuple]) -> list['Waypoint']:
        """
        Build Records
        """
        waypoints = []
        for geom in geometries:
            geoms = get_geoms_iter(geom)
            # noinspection PyTypeChecker
            waypoints.extend(super()._build_records(geoms, attributes))
        return waypoints
    # End _build_records method
# End QueryFeaturesToGPXMultiPoint class


TO_GPX: dict[str, Type[AbstractQueryFeaturesToGPX]] = {
    ShapeType.point: QueryFeaturesToGPXPoint,
    ShapeType.multi_point: QueryFeaturesToGPXMultiPoint,
    ShapeType.linestring: QueryFeaturesToGPXLineString,
    ShapeType.multi_linestring: QueryFeaturesToGPXMultiLineString,
}


if __name__ == '__main__':  # pragma: no cover
    pass
