# -*- coding: utf-8 -*-
"""
Test on base functionality
"""

from pytest import mark
from fudgeo import Field
from fudgeo.enumeration import SQLFieldType

from spyops.query.extract import QuerySplitByAttributes


pytestmark = [mark.query]


@mark.parametrize('name, fix_name, count, inserts, selects', [
    ('cities', 'world_tables', 11,
     'CITY_NAME, GMI_ADMIN, ADMIN_NAME, FIPS_CNTRY, CNTRY_NAME, STATUS, POP, POP_RANK, POP_CLASS, PORT_ID, POP_SOURCE',
     'CITY_NAME, GMI_ADMIN, ADMIN_NAME, FIPS_CNTRY, CNTRY_NAME, STATUS, POP, POP_RANK, POP_CLASS, PORT_ID, POP_SOURCE'),
    ('lakes_a', 'world_features', 8,
     'SHAPE, FEATURE_ID, PART_ID, NAME, SURF_ELEV, DEPTH, SQMI, SQKM',
     'SHAPE "[Polygon]", FEATURE_ID, PART_ID, NAME, SURF_ELEV, DEPTH, SQMI, SQKM'),
])
def test_field_names_and_count(request, name, fix_name, count, inserts, selects):
    """
    Test _field_names_and_count
    """
    geo = request.getfixturevalue(fix_name)
    element = geo[name]
    fields = [Field('a', data_type=SQLFieldType.text)]
    result = QuerySplitByAttributes(element, fields)._field_names_and_count(element)
    field_count, insert_field_names, select_field_names = result
    assert field_count == count
    assert insert_field_names == inserts
    assert select_field_names == selects
# End test_field_names_and_count function


if __name__ == '__main__':  # pragma: no cover
    pass
