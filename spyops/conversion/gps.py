# -*- coding: utf-8 -*-
"""
GPS
"""


from pathlib import Path
from typing import TYPE_CHECKING

from fudgeo.enumeration import GeometryType

from spyops.query.conversion.gps import TO_GPX
from spyops.shared.field import DATES, NUMBERS, TEXTS
from spyops.shared.hint import OPT_FIELD, OPT_FIELD_STR
from spyops.shared.keywords import (
    DATE_FIELD, DESCRIPTION_FIELD, EXT_GPX, NAME_FIELD, SOURCE, TARGET, Z_FIELD)
from spyops.validation import (
    validate_feature_class, validate_field, validate_file)


__all__ = ['features_to_gpx']


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass


@validate_feature_class(SOURCE, geometry_types=(
        GeometryType.point, GeometryType.multi_point,
        GeometryType.linestring, GeometryType.multi_linestring))
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


if __name__ == '__main__':  # pragma: no cover
    pass
