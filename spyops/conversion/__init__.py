# -*- coding: utf-8 -*-
"""
Package Initialization
"""


from spyops.conversion.geopackage import (
    export_features, export_table, feature_class_to_geopackage,
    table_to_geopackage)
from spyops.conversion.gps import features_to_gpx, gpx_to_features
from spyops.conversion.json import features_to_geojson, geojson_to_features
from spyops.shared.enumeration import GeoJSONGeometryType
from spyops.shared.sort import Ascending, Descending


__all__ = [
    'export_features',
    'export_table',
    'feature_class_to_geopackage',
    'table_to_geopackage',

    'features_to_gpx',
    'gpx_to_features',

    'features_to_geojson',
    'geojson_to_features',

    'GeoJSONGeometryType',

    'Ascending',
    'Descending',
]


if __name__ == '__main__':  # pragma: no cover
    pass
