# -*- coding: utf-8 -*-
"""
JSON
"""


from pathlib import Path
from typing import TYPE_CHECKING

from spyops.query.conversion.json import QueryFeaturesToGeoJSON
from spyops.shared.keywords import TARGET
from spyops.shared.constant import EXT_GEOJSON
from spyops.validation import validate_file, validate_source_feature_class


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass


__all__ = ['features_to_geojson']


@validate_source_feature_class()
@validate_file(TARGET, extension=EXT_GEOJSON)
def features_to_geojson(source: 'FeatureClass', target: Path | str, *,
                        as_wgs84: bool = True, formatted: bool = False,
                        include_z: bool = False, include_m: bool = False,
                        use_aliases: bool = False,
                        where_clause: str = '') -> Path:
    """
    Features to GeoJSON

    Convert a feature class to GeoJSON. The geometry and attributes of the
    feature class are included in the output.

    The following options are supported:

    * Convert coordinates to WGS84 (default and recommended for GeoJSON)
    * Use formatted JSON output (default is compact)
    * Include Z values in the target if present in the source
      (default is to exclude Z)
    * Include M values in the target if present in the source
      (default is to exclude M)
    * Use aliases instead of field names for attributes in the target
      (default is use field names)
    * Subset the features to be included in the target using a where clause
    """
    target: Path
    query = QueryFeaturesToGeoJSON(
        source, as_wgs84=as_wgs84, include_z=include_z, include_m=include_m,
        use_aliases=use_aliases, where_clause=where_clause)
    return query.export(target, formatted=formatted)
# End features_to_geojson function


if __name__ == '__main__':  # pragma: no cover
    pass
