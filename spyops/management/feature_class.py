# -*- coding: utf-8 -*-
"""
Data Management for Feature Classes
"""


from typing import TYPE_CHECKING

from fudgeo.enumeration import ShapeType
from numpy import isfinite

from spyops.geometry.extent import extent_from_index_or_geometry
from spyops.shared.constant import SOURCE
from spyops.shared.element import create_feature_class as _create_feature_class
from spyops.shared.hint import ELEMENT, FIELDS, GPKG
from spyops.shared.util import make_valid_name
from spyops.validation import (
    validate_element, validate_feature_class, validate_geopackage,
    validate_result)


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass, SpatialReferenceSystem


__all__ = ['recalculate_feature_class_extent', 'create_feature_class',
           'delete_features']


@validate_feature_class(SOURCE)
def recalculate_feature_class_extent(source: 'FeatureClass') -> 'FeatureClass':
    """
    Recalculate Extent of Feature Class

    Recalculates the extent of a feature class and stores the results in the
    GeoPackage internal tables.
    """
    extent = extent_from_index_or_geometry(source)
    if isfinite(extent).all():
        source.extent = extent
    return source
# End recalculate_feature_class_extent function


@validate_geopackage()
def create_feature_class(geopackage: GPKG, name: str,
                         srs: 'SpatialReferenceSystem',
                         *, fields: FIELDS = (), description: str = '',
                         shape_type: str = ShapeType.polygon,
                         z_enabled: bool = False,
                         m_enabled: bool = False) -> 'FeatureClass':
    """
    Create Feature Class

    Create a new feature class in a geopackage with the specified shape type,
    spatial reference, fields, and optional description.
    """
    name = make_valid_name(name, prefix='fc')
    return _create_feature_class(
        geopackage, name=name, srs=srs, fields=fields, description=description,
        shape_type=shape_type, z_enabled=z_enabled, m_enabled=m_enabled)
# End create_feature_class function


@validate_result()
@validate_element(SOURCE, has_content=False)
def delete_features(source: ELEMENT, *, where_clause: str = '') -> ELEMENT:
    """
    Delete rows from a Table or Feature Class

    Deletes rows from a table or feature class using a where clause (optional).
    """
    source.delete(where_clause=where_clause)
    return source
# End delete_features function


if __name__ == '__main__':  # pragma: no cover
    pass
