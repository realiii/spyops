# -*- coding: utf-8 -*-
"""
Query classes for conversion.json
"""


from functools import cache, cached_property
from json import dump
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from fudgeo import FeatureClass, MemoryGeoPackage

from spyops.crs.authority import to_authority
from spyops.crs.constant import WGS84
from spyops.crs.util import srs_from_crs
from spyops.environment.core import HasZM
from spyops.environment.core import ZMConfig
from spyops.query.base import BaseQuerySelect
from spyops.shared.constant import EMPTY, FEATURE, FEATURE_COLLECTION
from spyops.shared.field import (
    get_geometry_column_name, make_field_names,
    validate_fields)
from spyops.shared.keywords import (
    CRS_KEY, FEATURES_KEY, GEOMETRY_KEY,
    HASM_KEY, HASZ_KEY, ID_KEY, PROPERTIES_KEY, TYPE_KEY)
from spyops.shared.records import select_transform

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


if __name__ == '__main__':  # pragma: no cover
    pass
