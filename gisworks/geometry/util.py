# -*- coding: utf-8 -*-
"""
Utility Functions
"""


from sqlite3 import Cursor
from typing import Any, TYPE_CHECKING

from fudgeo.constant import FETCH_SIZE
from fudgeo.context import ExecuteMany
from shapely.geometry.base import (
    BaseGeometry, BaseMultipartGeometry, GeometrySequence)
from shapely.io import from_wkb

from gisworks.shared.constant import GEOMS_ATTR
from gisworks.shared.util import extend_records

if TYPE_CHECKING:  # pragma: no cover
    from gisworks.geometry.config import GeometryConfig


def nada(value: Any) -> Any:
    """
    Nada
    """
    return value
# End nada function


def get_geoms(geom: BaseGeometry | BaseMultipartGeometry) -> GeometrySequence:
    """
    Get Geometries
    """
    return getattr(geom, GEOMS_ATTR)
# End get_geoms function


def filter_features(features: list[tuple]) -> list[tuple]:
    """
    Filter Features, removing empty
    """
    return [feature for feature in features if not feature[0].is_empty]
# End filter_features function


def to_shapely(features: list[tuple]) -> list:
    """
    To Shapely Geometry from Fudgeo
    """
    return [from_wkb(g.wkb) for g, *_ in features]
# End to_shapely function


def bulk_insert(cursor: Cursor, config: GeometryConfig,
                executor: ExecuteMany, insert_sql: str) -> None:
    """
    Bulk Insert
    """
    records = []
    while features := cursor.fetchmany(FETCH_SIZE):
        if not (features := filter_features(features)):
            continue
        geometries = to_shapely(features)
        results = [(g, attrs) for g, (_, *attrs) in zip(geometries, features)]
        extend_records(results, records=records, config=config)
        executor(sql=insert_sql, data=records)
        records.clear()
# End bulk_insert function


if __name__ == '__main__':  # pragma: no cover
    pass
