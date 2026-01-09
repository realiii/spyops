# -*- coding: utf-8 -*-
"""
Utility Functions
"""

from typing import Any

from shapely.geometry.base import (
    BaseGeometry, BaseMultipartGeometry, GeometrySequence)
from shapely.io import from_wkb

from gisworks.shared.constant import GEOMS_ATTR


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


if __name__ == '__main__':  # pragma: no cover
    pass
