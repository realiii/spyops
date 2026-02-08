# -*- coding: utf-8 -*-
"""
Data Management for Fields
"""


from collections import defaultdict

from spyops.shared.constant import ELEMENTS_ARG, FIELDS_ARG, SOURCE
from spyops.shared.hint import ELEMENT, ELEMENTS, FIELDS, FIELD_NAMES
from spyops.validation import (
    validate_element, validate_elements, validate_field)


__all__ = ['delete_field', 'add_fields']


@validate_element(SOURCE, has_content=False)
@validate_field(FIELDS_ARG, element_name=SOURCE)
def delete_field(source: ELEMENT, fields: FIELDS | FIELD_NAMES) -> ELEMENT:
    """
    Delete Fields from a Table or Feature Class

    Deletes one or more fields from a table or feature class.
    """
    source.drop_fields(fields)
    return source
# End delete_field function


@validate_element(SOURCE, has_content=False)
@validate_field(FIELDS_ARG, exists=False)
@validate_elements(ELEMENTS_ARG, has_content=False)
def add_fields(source: ELEMENT, *, fields: FIELDS = (),
               elements: ELEMENTS = ()) -> ELEMENT:
    """
    Add Fields to a Table or Feature Class

    Adds one or more fields to a table or feature class using the schemas
    of elements and / or explicitly defined fields.
    """
    if not fields and not elements:
        return source
    fields = list(fields)
    for element in elements:
        # noinspection PyProtectedMember
        fields.extend(element._validate_fields(element.fields))
    if not fields:
        return source
    grouped = defaultdict(list)
    for field in fields:
        grouped[field.name.casefold()].append(field)
    source.add_fields([f for f, *_ in grouped.values()])
    return source
# End add_fields function


if __name__ == '__main__':  # pragma: no cover
    pass
