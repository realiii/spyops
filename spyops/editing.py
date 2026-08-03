# -*- coding: utf-8 -*-
"""
Package Initialization
"""


from typing import TYPE_CHECKING

from fudgeo.constant import FETCH_SIZE
from fudgeo.context import ExecuteMany
from fudgeo.enumeration import ShapeType
from fudgeo.util import get_extent

from spyops.crs.unit import (
    DecimalDegrees, Degrees, Feet, FeetInternational, FeetUS, Kilometers,
    Kilometres, Meters, Metres, Miles, MilesInternational, MilesUS,
    NauticalMiles, NauticalMilesInternational, NauticalMilesUS, StatuteMiles,
    USNauticalMiles, USSurveyFeet, USSurveyMiles, USSurveyYards, Yards,
    YardsInternational, YardsUS)
from spyops.geometry.util import filter_features, to_shapely
from spyops.geometry.wa import simplify
from spyops.query.editing import QueryGeneralize
from spyops.shared.hint import UNIT_TOLERANCE
from spyops.shared.keywords import SOURCE, TOLERANCE
from spyops.shared.records import extend_records
from spyops.validation import (
    validate_linear_unit, validate_result, validate_source_feature_class)


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass


__all__ = [
    'generalize',

    'DecimalDegrees',
    'Degrees',
    'Feet',
    'FeetInternational',
    'FeetUS',
    'Kilometers',
    'Kilometres',
    'Meters',
    'Metres',
    'Miles',
    'MilesInternational',
    'MilesUS',
    'NauticalMiles',
    'NauticalMilesInternational',
    'NauticalMilesUS',
    'StatuteMiles',
    'USNauticalMiles',
    'USSurveyFeet',
    'USSurveyMiles',
    'USSurveyYards',
    'Yards',
    'YardsInternational',
    'YardsUS',
]


@validate_result()
@validate_source_feature_class(geometry_types=(
        ShapeType.linestring, ShapeType.multi_linestring,
        ShapeType.polygon, ShapeType.multi_polygon))
@validate_linear_unit(TOLERANCE, feature_class_name=SOURCE, as_number=True)
def generalize(source: 'FeatureClass', tolerance: UNIT_TOLERANCE, *,
               preserve_topology: bool = True,
               where_clause: str = '') -> 'FeatureClass':
    """
    Generalize

    Performs a Douglas-Peucker simplification of line or polygon features using
    the specified tolerance.  The simplification is performed in place with
    no undo.
    """
    records = []
    tolerance: float
    with QueryGeneralize(source, where_clause=where_clause) as query:
        config = query.geometry_config
        with (query.source.geopackage.connection as cin,
              ExecuteMany(connection=cin, table=query.target) as executor):
            cursor = cin.execute(query.select)
            while features := cursor.fetchmany(FETCH_SIZE):
                if not (features := filter_features(features)):
                    continue
                features, geometries = to_shapely(features, transformer=None)
                geometries = simplify(
                    geometries, tolerance=tolerance,
                    preserve_topology=preserve_topology)
                results = [(geom, (id_,)) for (_, id_), geom in
                           zip(features, geometries)]
                extend_records(results, records=records, config=config)
            updates = [(geom, id_) for id_, geom in records]
            executor(sql=query.insert, data=updates)
            cin.execute(query.update)
            query.source.extent = get_extent(query.source)
    return query.source
# End generalize function


if __name__ == '__main__':  # pragma: no cover
    pass
