# -*- coding: utf-8 -*-
"""
Query classes for conversion.json
"""


from abc import abstractmethod
from collections import defaultdict
from functools import cache, cached_property
from json import dump, load
from math import nan
from pathlib import Path
from typing import Any, Callable, Counter, Optional, TYPE_CHECKING, Type

from fudgeo import FeatureClass, Field, MemoryGeoPackage
from fudgeo.enumeration import ShapeType
from pyproj import CRS
from pyproj.exceptions import CRSError

from spyops.crs.authority import to_authority
from spyops.crs.constant import WGS84
from spyops.crs.util import from_authority, srs_from_crs
from spyops.environment.core import HasZM
from spyops.environment.core import ZMConfig
from spyops.geometry.lookup import FUDGEO_GEOMETRY_LOOKUP
from spyops.geometry.util import to_shapely
from spyops.query.base import AbstractSourceQuery, BaseQuerySelect
from spyops.shared.constant import (
    COLON, EMPTY, FEATURE, FEATURE_COLLECTION, UNDERSCORE)
from spyops.shared.enumeration import GeoJSONGeometryType
from spyops.shared.field import (
    find_field_data_type, get_geometry_column_name, make_field_names,
    make_unique_fields, validate_fields)
from spyops.shared.hint import FIELDS, NAMES, POINT_TYPE
from spyops.shared.keywords import (
    COORDINATES_KEY, CRS_KEY, FEATURES_KEY, GEOMETRY_KEY, HASM_KEY, HASZ_KEY,
    ID_KEY, NAME_KEY, PROPERTIES_KEY, TYPE_KEY)
from spyops.shared.records import select_transform
from spyops.shared.util import make_valid_field_name


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import SpatialReferenceSystem


class QueryFeaturesToGeoJSON(BaseQuerySelect):
    """
    Query Features to GeoJSON
    """
    def __init__(self, source: FeatureClass, as_wgs84: bool, include_z: bool,
                 include_m: bool, use_aliases: bool, where_clause: str) -> None:
        """
        Initialize the QueryFeaturesToGeoJSON class
        """
        self._scratch: MemoryGeoPackage = MemoryGeoPackage.create()

        super().__init__(
            source, target=FeatureClass(self._scratch, name='json_target'),
            where_clause=where_clause)
        self._as_wgs84: bool = as_wgs84
        self._include_z: bool = include_z and source.has_z
        self._include_m: bool = include_m and source.has_m
        self._use_aliases: bool = use_aliases
    # End init built-in

    @cache
    def _field_names_and_count(self, element: FeatureClass) -> tuple[int, str, str]:
        """
        Overload to ensure that the primary key is included in attributes,
        do not need insert names or count
        """
        fields = validate_fields(
            element, fields=element.fields, exclude_primary=False)
        select_names = make_field_names(fields)
        geom_type = get_geometry_column_name(
            element, include_geom_type=True)
        select_names = self._concatenate(geom_type, select_names)
        return 0, EMPTY, select_names
    # End _field_names_and_count method

    @cached_property
    def spatial_reference_system(self) -> Optional['SpatialReferenceSystem']:
        """
        Spatial Reference System
        """
        if self._as_wgs84:
            return srs_from_crs(WGS84)
        return super().spatial_reference_system
    # End spatial_reference_system property

    def _get_attribute_names(self) -> tuple[str, ...]:
        """
        Get Attribute Names
        """
        fields = validate_fields(
            self.source, fields=self.source.fields, exclude_primary=False)
        if not self._use_aliases:
            return tuple(f.name for f in fields)
        return tuple(f.alias or f.name for f in fields)
    # End _get_attribute_names method

    @staticmethod
    def _export_to_path(path: Path, data: dict, formatted: bool) -> Path:
        """
        Export to Path
        """
        if formatted:
            indent = 4
        else:
            indent = None
        with path.open('w') as fout:
            dump(data, fp=fout, indent=indent)
        return path
    # End _export_to_path method

    def _build_data(self) -> dict:
        """
        Build Data
        """
        data = {}
        self._add_zm_flags(data)
        self._add_feature_collection(data)
        self._add_crs(data)
        self._add_features(data)
        return data
    # End _build_data method

    def _add_zm_flags(self, data: dict) -> None:
        """
        Add ZM Flags
        """
        for key, value in zip((HASZ_KEY, HASM_KEY), self._has_zm):
            if not value:
                continue
            data[key] = value
    # End _add_zm_flags method

    @staticmethod
    def _add_feature_collection(data: dict) -> None:
        """
        Add Feature Collection
        """
        data[TYPE_KEY] = FEATURE_COLLECTION
    # End _add_feature_collection method

    def _add_crs(self, data: dict) -> None:
        """
        Add CRS
        """
        if not (srs := self.spatial_reference_system):
            return
        if srs.srs_id == 4326:
            return
        if auth := to_authority(self.source_crs):
            data[CRS_KEY] = auth.as_label()
    # End _add_crs method

    def _add_features(self, data: dict) -> None:
        """
        Add Features
        """
        features = []
        keys = self._get_attribute_names()
        ids = iter(range(1, len(self.source) + 1))
        for records in select_transform(self):
            if not records:
                continue
            features.extend(
                {TYPE_KEY: FEATURE,
                 ID_KEY: next(ids),
                 GEOMETRY_KEY: geom.__geo_interface__,
                 PROPERTIES_KEY: dict(zip(keys, attrs))}
                for geom, *attrs in records)
        data[FEATURES_KEY] = features
    # End _add_features method

    @property
    def _has_zm(self) -> HasZM:
        """
        Has ZM
        """
        return HasZM(has_z=self._include_z, has_m=self._include_m)
    # End _has_zm property

    @cached_property
    def zm_config(self) -> ZMConfig:
        """
        ZM Configuration
        """
        diff_z = self.source.has_z != self._include_z
        diff_m = self.source.has_m != self._include_m
        return ZMConfig(is_different=diff_z or diff_m,
                        z_enabled=self._include_z, m_enabled=self._include_m)
    # End zm_config property

    def export(self, path: Path, formatted: bool) -> Path:
        """
        Build JSON data and Export to Path
        """
        data = self._build_data()
        path = self._export_to_path(path, data=data, formatted=formatted)
        if conn := self._scratch.connection:
            conn.close()
        return path
    # End export method
# End QueryFeaturesToGeoJSON class


class AbstractQueryGeoJSONToFeatures(AbstractSourceQuery):
    """
    Abstract Query GeoJSON to Features
    """
    def __init__(self, source: Path, target: 'FeatureClass') -> None:
        """
        Initialize the AbstractQueryGeoJSONToFeatures class
        """
        # noinspection PyTypeChecker
        super().__init__(source=None, target=target)
        self._source: Path = source
    # End init built-in

    @cached_property
    def _data(self) -> dict:
        """
        Data
        """
        with self._source.open() as fin:
            return load(fin)
    # End _data property

    @cached_property
    def _fields(self) -> FIELDS:
        """
        FIELDS
        """
        fields = self._get_fields_from_source()
        names = [f.name.casefold() for f in fields]
        if len(names) == len(set(names)):
            return tuple(fields)
        return self._make_unique_fields(fields, names)
    # End _fields property

    @staticmethod
    def _make_unique_fields(fields: list[Field], names: list[str]) -> FIELDS:
        """
        Make Unique Fields
        """
        visited = set()
        names = [n for n, count in Counter(names).items() if count > 1]
        for i, field in enumerate(fields):
            lower = field.name.casefold()
            if lower not in names:
                continue
            if lower not in visited:
                visited.add(lower)
                continue
            field, = make_unique_fields(fields, [field])
            # noinspection PyTypeChecker
            fields[i] = field
        return tuple(fields)
    # End _make_unique_fields method

    def _get_fields_from_source(self) -> list[Field]:
        """
        Get Fields from Source, guess the data type of the field based on the
        first 100 records of the data.
        """
        data = defaultdict(list)
        features = self._filtered_features()[:100]
        for feature in features:
            for key, value in feature[PROPERTIES_KEY].items():
                data[key].append(value)
        if not data:
            return []
        _, *field_names = data
        data_types = find_field_data_type(field_names, data=data)
        field_names = [make_valid_field_name(name) for name in field_names]
        return [Field(name=name, data_type=data_type)
                for name, data_type in zip(field_names, data_types)]
    # End _get_fields_from_source method

    def _get_unique_fields(self) -> FIELDS:
        """
        Get Unique Fields
        """
        return self._fields
    # End _get_unique_fields method

    @cached_property
    def source_crs(self) -> CRS:
        """
        Source CRS
        """
        code = self._data.get(CRS_KEY, {}).get(PROPERTIES_KEY, {}).get(NAME_KEY)
        if code is None:
            return WGS84
        if COLON in code:
            if crs := from_authority(*code.split(COLON, 2)[:2]):
                return crs
        try:
            return CRS(code)
        except CRSError:
            return WGS84
    # End source_crs property

    @cached_property
    def source_transformer(self) -> Callable | None:
        """
        Source Transformer
        """
        return None
    # End source_transformer property

    @cached_property
    def spatial_reference_system(self) -> 'SpatialReferenceSystem':
        """
        Spatial Reference System, the output coordinate system of the query
        which is determined by the output coordinate system of the analysis
        environment and if not set, the spatial reference system of the source.
        """
        return srs_from_crs(self.source_crs)
    # End spatial_reference_system property

    @property
    def _has_zm(self) -> HasZM:
        """
        Has ZM
        """
        has_z = self._data.get(HASZ_KEY, False)
        has_m = self._data.get(HASM_KEY, False)
        return HasZM(has_z=has_z, has_m=has_m)
    # End _has_zm property

    @property
    def insert(self) -> str:
        """
        Insert
        """
        elm = self.target
        field_count, insert_field_names, _ = self._field_names_and_count(elm)
        return self._make_insert(
            elm.escaped_name, field_names=insert_field_names,
            field_count=field_count)
    # End insert property

    @cached_property
    def zm_config(self) -> ZMConfig:
        """
        ZM Configuration
        """
        z_enabled, m_enabled = self._has_zm
        return ZMConfig(
            is_different=False, z_enabled=z_enabled, m_enabled=m_enabled)
    # End zm_config property

    @cache
    def _filtered_features(self) -> list[dict]:
        """
        Filtered Features
        """
        if not (features := self._data.get(FEATURES_KEY, [])):
            return features
        if not (features := self._valid_features(features)):
            return features
        shape_types = {t.casefold() for t in self._filter_shape_types()}
        return [f for f in features
                if f[GEOMETRY_KEY][TYPE_KEY].casefold() in shape_types]
    # End _filtered_features method

    @staticmethod
    def _valid_features(features: list[dict]) -> list[dict]:
        """
        Get the valid features from the GeoJSON data.
        """
        type_key = TYPE_KEY
        geom_key = GEOMETRY_KEY
        feature = FEATURE.casefold()
        features = [f for f in features
                    if f.get(type_key, EMPTY).casefold() == feature]
        features = [f for f in features if PROPERTIES_KEY in f]
        features = [f for f in features
                    if geom_key in f and type_key in f[geom_key]]
        features = [f for f in features if type_key in f[geom_key]]
        return [f for f in features if f[geom_key].get(COORDINATES_KEY)]
    # End _valid_features method

    def _get_geometry_class(self) -> Any:
        """
        Get Geometry Class
        """
        has_z, has_m = self._has_zm
        shape_type = self._get_target_shape_type()
        return FUDGEO_GEOMETRY_LOOKUP[shape_type][has_z, has_m]
    # End _get_geometry_class method

    def features(self, path: Path) -> list[tuple]:
        """
        Features from JSON File
        """
        records = []
        if not (features := self._filtered_features()):
            return records
        cls, count, srs_id = self._get_feature_meta()
        for feature in features:
            coords = feature[GEOMETRY_KEY][COORDINATES_KEY]
            coords = self._adjust_coordinates(coords, count)
            geom = cls(coords, srs_id=srs_id)
            _, *attrs = feature[PROPERTIES_KEY].values()
            records.append((geom, *attrs))
        return self._make_shapely_records(records)
    # End features method

    @staticmethod
    def _make_shapely_records(records: list[tuple]) -> list[tuple]:
        """
        Make Shapely Records
        """
        features, geometries = to_shapely(
            records, transformer=None)
        return [(g, *attrs) for g, (_, *attrs) in zip(geometries, features)]
    # End _make_shapely_records method

    def _filter_shape_types(self) -> NAMES:
        """
        Filter Shape Types
        """
        return self._get_target_shape_type(),
    # End _filter_shape_types method

    def _get_feature_meta(self) -> tuple[Any, int, int]:
        """
        Get Feature Meta, Class, Count, and SRS ID
        """
        count = 2 + sum(self._has_zm)
        cls = self._get_geometry_class()
        srs_id = self.spatial_reference_system.srs_id
        return cls, count, srs_id
    # End _get_feature_meta method

    @abstractmethod
    def _adjust_coordinates(self, coordinates: list, count: int) -> list:
        """
        Adjusts coordinates to the correct dimension
        """
        pass
    # End _adjust_coordinates method

    @staticmethod
    def _extend_and_slice(coordinates: list, count: int) -> list:
        """
        Extend and Slice coordinates to the correct dimension
        """
        if len(coordinates) != count:
            coordinates = [*coordinates, nan, nan]
        return coordinates[:count]
    # End _extend_and_slice method
# End AbstractQueryGeoJSONToFeatures class


class AbstractQueryGeoJSONToFeaturesMulti(AbstractQueryGeoJSONToFeatures):
    """
    Abstract Query GeoJSON to Features Multi-part
    """
    def features(self, path: Path) -> list[tuple]:
        """
        Features from JSON File
        """
        records = []
        if not (features := self._filtered_features()):
            return records
        cls, count, srs_id = self._get_feature_meta()
        for feature in features:
            geometry = feature[GEOMETRY_KEY]
            coords = geometry[COORDINATES_KEY]
            if not geometry[TYPE_KEY].casefold().startswith('m'):
                coords = [coords]
            coords = self._adjust_coordinates(coords, count)
            geom = cls(coords, srs_id=srs_id)
            _, *attrs = feature[PROPERTIES_KEY].values()
            records.append((geom, *attrs))
        return self._make_shapely_records(records)
    # End features method

    @abstractmethod
    def _adjust_coordinates(self, coordinates: list, count: int) -> list:
        """
        Adjusts coordinates to the correct dimension
        """
        pass
    # End _adjust_coordinates method
# End AbstractQueryGeoJSONToFeaturesMulti class


class QueryGeoJSONToFeaturesPoint(AbstractQueryGeoJSONToFeatures):
    """
    Query GeoJSON to Features Point
    """
    def _get_target_shape_type(self) -> str:
        """
        Get Target Shape Type
        """
        return ShapeType.point
    # End _get_target_shape_type method

    def _filter_shape_types(self) -> NAMES:
        """
        Filter Shape Types
        """
        return self._get_target_shape_type(),
    # End _filter_shape_types method

    def features(self, path: Path) -> list[tuple]:
        """
        Features from JSON File
        """
        records = []
        if not (features := self._filtered_features()):
            return records
        cls, count, srs_id = self._get_feature_meta()
        for feature in features:
            coords = feature[GEOMETRY_KEY][COORDINATES_KEY]
            coords = self._adjust_coordinates(coords, count)
            _, *attrs = feature[PROPERTIES_KEY].values()
            # noinspection PyTypeChecker
            geom = cls.from_tuple(coords, srs_id=srs_id)
            records.append((geom, *attrs))
        return self._make_shapely_records(records)
    # End features method

    def _adjust_coordinates(self, coordinates: list, count: int) -> list:
        """
        Adjusts coordinates to the correct dimension
        """
        return self._extend_and_slice(coordinates, count)
    # End _adjust_coordinates method

    def _get_geometry_class(self) -> POINT_TYPE:
        """
        Get Geometry Class
        """
        return super()._get_geometry_class()
    # End _get_geometry_class method
# End QueryGeoJSONToFeaturesPoint class


class QueryGeoJSONToFeaturesMultiPoint(AbstractQueryGeoJSONToFeaturesMulti):
    """
    Query GeoJSON to Features MultiPoint
    """
    def _get_target_shape_type(self) -> str:
        """
        Get Target Shape Type
        """
        return ShapeType.multi_point
    # End _get_target_shape_type method

    def _filter_shape_types(self) -> NAMES:
        """
        Filter Shape Types
        """
        return self._get_target_shape_type(), ShapeType.point
    # End _filter_shape_types method

    def _adjust_coordinates(self, coordinates: list, count: int) -> list:
        """
        Adjusts coordinates to the correct dimension
        """
        return [self._extend_and_slice(coords, count) for coords in coordinates]
    # End _adjust_coordinates method
# End QueryGeoJSONToFeaturesMultiPoint class


class QueryGeoJSONToFeaturesLineString(AbstractQueryGeoJSONToFeatures):
    """
    Query GeoJSON to Features LineString
    """
    def _get_target_shape_type(self) -> str:
        """
        Get Target Shape Type
        """
        return ShapeType.linestring
    # End _get_target_shape_type method

    def _adjust_coordinates(self, coordinates: list, count: int) -> list:
        """
        Adjusts coordinates to the correct dimension
        """
        return [self._extend_and_slice(coords, count) for coords in coordinates]
    # End _adjust_coordinates method
# End QueryGeoJSONToFeaturesLineString class


class QueryGeoJSONToFeaturesMultiLineString(
        AbstractQueryGeoJSONToFeaturesMulti):
    """
    Query GeoJSON to Features Multi-LineString
    """
    def _get_target_shape_type(self) -> str:
        """
        Get Target Shape Type
        """
        return ShapeType.multi_linestring
    # End _get_target_shape_type method

    def _filter_shape_types(self) -> NAMES:
        """
        Filter Shape Types
        """
        return self._get_target_shape_type(), ShapeType.linestring
    # End _filter_shape_types method

    def _adjust_coordinates(self, coordinates: list, count: int) -> list:
        """
        Adjusts coordinates to the correct dimension
        """
        adjusted = []
        for line in coordinates:
            adjusted.append(
                [self._extend_and_slice(coords, count) for coords in line])
        return adjusted
    # End _adjust_coordinates method
# End QueryGeoJSONToFeaturesMultiLineString class


class QueryGeoJSONToFeaturesPolygon(AbstractQueryGeoJSONToFeatures):
    """
    Query GeoJSON to Features Polygon
    """
    def _get_target_shape_type(self) -> str:
        """
        Get Target Shape Type
        """
        return ShapeType.polygon
    # End _get_target_shape_type method

    def _filter_shape_types(self) -> NAMES:
        """
        Filter Shape Types
        """
        return self._get_target_shape_type(),
    # End _filter_shape_types method

    def _adjust_coordinates(self, coordinates: list, count: int) -> list:
        """
        Adjusts coordinates to the correct dimension
        """
        adjusted = []
        for ring in coordinates:
            adjusted.append(
                [self._extend_and_slice(coords, count) for coords in ring])
        return adjusted
    # End _adjust_coordinates method
# End QueryGeoJSONToFeaturesPolygon class


class QueryGeoJSONToFeaturesMultiPolygon(AbstractQueryGeoJSONToFeaturesMulti):
    """
    Query GeoJSON to Features Multi-Polygon
    """
    def _get_target_shape_type(self) -> str:
        """
        Get Target Shape Type
        """
        return ShapeType.multi_polygon
    # End _get_target_shape_type method

    def _filter_shape_types(self) -> NAMES:
        """
        Filter Shape Types
        """
        return self._get_target_shape_type(), ShapeType.polygon
    # End _filter_shape_types method

    def _adjust_coordinates(self, coordinates: list, count: int) -> list:
        """
        Adjusts coordinates to the correct dimension
        """
        adjusted = []
        for poly in coordinates:
            adjusted_poly = []
            for ring in poly:
                adjusted_poly.append(
                    [self._extend_and_slice(coords, count) for coords in ring])
            adjusted.append(adjusted_poly)
        return adjusted
    # End _adjust_coordinates method
# End QueryGeoJSONToFeaturesMultiPolygon class


def geojson_query_factory(path: Path, geometry_type: GeoJSONGeometryType) \
        -> Type[AbstractQueryGeoJSONToFeatures]:
    """
    GeoJSON Query Factory
    """
    if geometry_type in FROM_JSON:
        return FROM_JSON[geometry_type]
    with path.open() as fin:
        data = load(fin)
    cls = QueryGeoJSONToFeaturesPoint
    if not (features := data.get(FEATURES_KEY, [])):
        return cls
    multi = 'multi'
    prefix = f'{multi}{UNDERSCORE}'
    types = ShapeType.point, ShapeType.linestring, ShapeType.polygon
    lut = {t.casefold(): f'{prefix}{t.casefold()}' for t in types}
    # noinspection PyProtectedMember
    features = AbstractQueryGeoJSONToFeatures._valid_features(features)
    shape_types = [f[GEOMETRY_KEY][TYPE_KEY].casefold() for f in features]
    counter = Counter(shape_types)
    for shape_type, _ in counter.most_common():
        shape_type = shape_type.casefold().replace(multi, prefix)
        multi_shape_type = lut.get(shape_type)
        if multi_shape_type is not None and multi_shape_type in counter:
            shape_type = multi_shape_type
        try:
            return FROM_JSON[GeoJSONGeometryType(shape_type)]
        except (ValueError, KeyError):
            continue
    return cls
# End geojson_query_factory function


FROM_JSON: dict[GeoJSONGeometryType, Type[AbstractQueryGeoJSONToFeatures]] = {
    GeoJSONGeometryType.POINT: QueryGeoJSONToFeaturesPoint,
    GeoJSONGeometryType.MULTI_POINT: QueryGeoJSONToFeaturesMultiPoint,
    GeoJSONGeometryType.LINESTRING: QueryGeoJSONToFeaturesLineString,
    GeoJSONGeometryType.MULTI_LINESTRING: QueryGeoJSONToFeaturesMultiLineString,
    GeoJSONGeometryType.POLYGON: QueryGeoJSONToFeaturesPolygon,
    GeoJSONGeometryType.MULTI_POLYGON: QueryGeoJSONToFeaturesMultiPolygon,
}


if __name__ == '__main__':  # pragma: no cover
    pass
