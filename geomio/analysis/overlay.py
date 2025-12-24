# -*- coding: utf-8 -*-
"""
Overlay
"""


from fudgeo import FeatureClass
from fudgeo.constant import FETCH_SIZE
from shapely import set_precision
from shapely.io import from_wkb

from geomio.shared.base import OverlayConfig
from geomio.shared.constant import OPERATOR, SOURCE, TARGET
from geomio.shared.field import GEOM_TYPE_POLYGONS
from geomio.shared.geometry import overlay_config
from geomio.shared.hint import XY_TOL
from geomio.shared.query import QueryErase
from geomio.shared.util import extend_records
from geomio.shared.validation import (
    validate_feature_class, validate_result, validate_same_crs,
    validate_xy_tolerance)


@validate_result()
@validate_same_crs(SOURCE, OPERATOR)
@validate_xy_tolerance()
@validate_feature_class(TARGET, exists=False)
@validate_feature_class(OPERATOR, geometry_types=GEOM_TYPE_POLYGONS)
@validate_feature_class(SOURCE)
def erase(source: FeatureClass, operator: FeatureClass, target: FeatureClass, *,
          xy_tolerance: XY_TOL = None) -> FeatureClass:
    """
    Erase

    Removes the portion of the input feature class that overlaps with the
    operator feature class.
    """
    query = QueryErase(source, target=target, operator=operator)
    if not query.has_intersection:
        return query.target_full
    records = []
    config = overlay_config(source, operator=operator)
    polygon = config.geometry
    _process_disjoint(query, config=config, xy_tolerance=xy_tolerance)
    with (query.target.geopackage.connection as cout,
          query.source.geopackage.connection as cin):
        cursor = cin.execute(query.select)
        while features := cursor.fetchmany(FETCH_SIZE):
            geometries = [from_wkb(g.wkb) for g, *_ in features]
            intersects = polygon.intersects(geometries)
            keepers = [f for f, i in zip(features, intersects) if not i]
            geoms = [g for g, i in zip(geometries, intersects) if not i]
            if xy_tolerance is not None:
                geoms = set_precision(geoms, grid_size=xy_tolerance)
            results = [(g, geom, attrs) for geom, (g, *attrs) in
                       zip(geoms, keepers)]
            extend_records(results, records=records, config=config)
            changers = [f for f, i in zip(features, intersects) if i]
            geoms = [g for g, i in zip(geometries, intersects) if i]
            results = [(g, geom.difference(polygon, grid_size=xy_tolerance), attrs)
                       for geom, (g, *attrs) in zip(geoms, changers)]
            extend_records(results, records=records, config=config)
            cout.executemany(query.insert, records)
            records.clear()
    return query.target
# End erase function


def _process_disjoint(query: QueryErase, config: OverlayConfig,
                      xy_tolerance: XY_TOL) -> None:
    """
    Process Disjoint Features
    """
    if not query.select_disjoint:
        return
    records = []
    with (query.target.geopackage.connection as cout,
          query.source.geopackage.connection as cin):
        cursor = cin.execute(query.select_disjoint)
        while features := cursor.fetchmany(FETCH_SIZE):
            if xy_tolerance is None:
                cout.executemany(query.insert, features)
            else:
                geometries = [from_wkb(g.wkb) for g, *_ in features]
                geometries = set_precision(
                    geometries, grid_size=xy_tolerance)
                results = [(g, geom, attrs) for geom, (g, *attrs) in
                           zip(geometries, features)]
                extend_records(results, records=records, config=config)
                cout.executemany(query.insert, records)
                records.clear()
# End _process_disjoint function


if __name__ == '__main__':  # pragma: no cover
    pass
