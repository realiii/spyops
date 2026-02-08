# -*- coding: utf-8 -*-
"""
Data Management for Fields
"""


from spyops.shared.constant import FIELDS_ARG, SOURCE
from spyops.shared.hint import ELEMENT, FIELDS, FIELD_NAMES
from spyops.validation import validate_element, validate_field


__all__ = ['delete_field']


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


if __name__ == '__main__':  # pragma: no cover
    pass
