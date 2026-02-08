# -*- coding: utf-8 -*-
"""
Data Management for Indexes
"""


from typing import TYPE_CHECKING

from spyops.shared.constant import INDEX_FIELDS, SOURCE
from spyops.shared.field import TEXT_AND_NUMBERS
from spyops.shared.hint import ELEMENT, FIELDS, FIELD_NAMES
from spyops.validation import (
    validate_element, validate_feature_class, validate_field)


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass


__all__ = ['add_spatial_index', 'remove_spatial_index', 'add_attribute_index',
           'remove_attribute_index']


@validate_feature_class(SOURCE, has_content=False)
def add_spatial_index(source: 'FeatureClass') -> 'FeatureClass':
    """
    Add Spatial Index

    Creates a spatial index on the input feature class.  If a spatial index
    already exists, it is not recreated.
    """
    source.add_spatial_index()
    return source
# End add_spatial_index function


@validate_feature_class(SOURCE, has_content=False)
def remove_spatial_index(source: 'FeatureClass') -> 'FeatureClass':
    """
    Remove Spatial Index

    Removes the spatial index from the input feature class.  If no spatial
    index exists, no action is taken.
    """
    source.drop_spatial_index()
    return source
# End remove_spatial_index function


@validate_element(SOURCE, has_content=False)
@validate_field(INDEX_FIELDS, data_types=TEXT_AND_NUMBERS, element_name=SOURCE)
def add_attribute_index(source: ELEMENT, name: str,
                        index_fields: FIELDS | FIELD_NAMES, *,
                        is_unique: bool = False,
                        is_ascending: bool = True) -> ELEMENT:
    """
    Add Attribute Index

    Creates an attribute index on the input table or feature class.  If an
    attribute index already exists, it is not recreated.
    """
    source.add_attribute_index(
        name, fields=index_fields, is_unique=is_unique,
        is_ascending=is_ascending)
    return source
# End add_attribute_index function


@validate_element(SOURCE, has_content=False)
def remove_attribute_index(source: ELEMENT, name: str) -> ELEMENT:
    """
    Remove Attribute Index

    Removes the attribute index from the input table or feature class.  If no
    attribute index exists, no action is taken.
    """
    source.drop_attribute_index(name)
    return source
# End remove_attribute_index function


if __name__ == '__main__':  # pragma: no cover
    pass
