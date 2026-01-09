# -*- coding: utf-8 -*-
"""
Utility Functions
"""

from typing import Any

from shapely.geometry.base import (
    BaseGeometry, BaseMultipartGeometry, GeometrySequence)

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


if __name__ == '__main__':  # pragma: no cover
    pass
