# -*- coding: utf-8 -*-
"""
GPS
"""


from pathlib import Path
from typing import TYPE_CHECKING

from fudgeo.enumeration import ShapeType

from spyops.conversion.util import _to_features
from spyops.query.conversion.gps import FROM_GPX, TO_GPX
from spyops.shared.field import DATES, NUMBERS, TEXTS
from spyops.shared.hint import OPT_FIELD, OPT_FIELD_STR
from spyops.shared.keywords import (
    DATE_FIELD, DESCRIPTION_FIELD, NAME_FIELD, SOURCE, TARGET, Z_FIELD)
from spyops.shared.constant import EXT_GPX
from spyops.validation import (
    validate_feature_class, validate_field, validate_file,
    validate_result, validate_target_feature_class)


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass


__all__ = ['features_to_gpx', 'gpx_to_features']


@validate_feature_class(SOURCE, geometry_types=(
        ShapeType.point, ShapeType.multi_point,
        ShapeType.linestring, ShapeType.multi_linestring))
@validate_file(TARGET, extension=EXT_GPX)
@validate_field(NAME_FIELD, element_name=SOURCE, single=True,
                is_optional=True, data_types=TEXTS)
@validate_field(DESCRIPTION_FIELD, element_name=SOURCE, single=True,
                is_optional=True, data_types=TEXTS)
@validate_field(Z_FIELD, element_name=SOURCE, single=True,
                is_optional=True, data_types=NUMBERS)
@validate_field(DATE_FIELD, element_name=SOURCE, single=True,
                is_optional=True, data_types=DATES)
def features_to_gpx(source: 'FeatureClass', target: Path | str, *,
                    name_field: OPT_FIELD_STR = None,
                    description_field: OPT_FIELD_STR = None,
                    z_field: OPT_FIELD_STR = None,
                    date_field: OPT_FIELD_STR = None,
                    where_clause: str = '') -> Path:
    """
    Features to GPX

    Convert features to the GPX format. Supported geometry types are point,
    multipoint, linestring, and multilinestring.  Output coordinates will be
    in WGS84.  Features can be filtered by extent and / or using a where clause.
    """
    target: Path
    z_field: OPT_FIELD
    name_field: OPT_FIELD
    date_field: OPT_FIELD
    description_field: OPT_FIELD
    cls = TO_GPX[source.shape_type]
    query = cls(source, name_field=name_field, z_field=z_field,
                description_field=description_field, date_field=date_field,
                where_clause=where_clause)
    return query.export(target)
# End features_to_gpx function


@validate_result()
@validate_file(SOURCE, is_output=False)
@validate_target_feature_class()
def gpx_to_features(source: Path | str, target: 'FeatureClass', *,
                    as_points: bool = True) -> 'FeatureClass':
    """
    GPX to Features

    Convert a GPX file to point features or line features.  The point option
    converts waypoints and trackpoints, the line option (as_points=False)
    converts tracks.
    """
    source: Path
    query = FROM_GPX[as_points](target=target)
    return _to_features(source, query=query)
# End gpx_to_features function


if __name__ == '__main__':  # pragma: no cover
    pass
