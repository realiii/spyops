# -*- coding: utf-8 -*-
"""
Field
"""


from fudgeo import FeatureClass, Field
from fudgeo.constant import COMMA_SPACE
from fudgeo.enumeration import GeometryType, SQLFieldType

from geomio.shared.hint import ELEMENT, FIELDS, FIELD_NAMES, NAMES


GEOM_TYPE_POINTS: NAMES = GeometryType.point, GeometryType.multi_point
GEOM_TYPE_LINES: NAMES = GeometryType.linestring, GeometryType.multi_linestring
GEOM_TYPE_POLYGONS: NAMES = GeometryType.polygon, GeometryType.multi_polygon


ALIAS_TYPE_LUT: dict[NAMES, str] = {
    (SQLFieldType.boolean.casefold(),): SQLFieldType.boolean,
    (SQLFieldType.blob.casefold(),): SQLFieldType.blob,
    (SQLFieldType.tinyint.casefold(),): SQLFieldType.tinyint,
    (SQLFieldType.smallint.casefold(),): SQLFieldType.smallint,
    (SQLFieldType.mediumint.casefold(),): SQLFieldType.mediumint,
    ('char', 'varchar', 'tinytext', SQLFieldType.text.casefold(), 'mediumtext',
     'longtext', 'nchar', 'nvarchar', 'clob'): SQLFieldType.text,
    ('numeric', 'decimal', SQLFieldType.real.casefold()): SQLFieldType.real,
    (SQLFieldType.double.casefold(), 'double precision'): SQLFieldType.double,
    (SQLFieldType.float.casefold(),): SQLFieldType.float,
    (SQLFieldType.date.casefold(),): SQLFieldType.date,
    (SQLFieldType.datetime.casefold(),): SQLFieldType.datetime,
    ('time', SQLFieldType.timestamp.casefold()): SQLFieldType.timestamp,
    ('int', SQLFieldType.integer.casefold(), 'bigint', 'int2',
     'int4', 'int8'): SQLFieldType.integer,
}
TYPE_ALIAS_LUT: dict[str, NAMES] = {
    v: k for k, v in ALIAS_TYPE_LUT.items()}


DATES: NAMES = SQLFieldType.date, SQLFieldType.datetime, SQLFieldType.timestamp
INTEGERS: NAMES = (SQLFieldType.tinyint, SQLFieldType.smallint,
                   SQLFieldType.mediumint, SQLFieldType.integer)
REALS: NAMES = SQLFieldType.float, SQLFieldType.double, SQLFieldType.real
TEXTS: NAMES = SQLFieldType.text,
NUMBERS: NAMES = (*INTEGERS, *REALS)
TEXT_AND_INTEGERS: NAMES = (*TEXTS, *INTEGERS)
TEXT_AND_NUMBERS: NAMES = (*TEXTS, *NUMBERS)
TEXT_AND_REALS: NAMES = (*TEXTS, *REALS)


def validate_fields(element: ELEMENT, fields: FIELDS | FIELD_NAMES,
                    exclude_geometry: bool = True,
                    exclude_primary: bool = True) -> FIELDS:
    """
    Validate Fields
    """
    keepers = []
    visited = set()
    field_lookup = {f.name.casefold(): f for f in element.fields}
    if not isinstance(fields, (list, tuple)):
        fields = fields,
    for f in fields:
        if not isinstance(f, (Field, str)):
            continue
        name = getattr(f, 'name', f).casefold()
        if name in visited:
            continue
        visited.add(name)
        field = field_lookup.get(name)
        if field is None:
            continue
        keepers.append(field)
    return exclude_special(
        element, fields=keepers, exclude_primary=exclude_primary,
        exclude_geometry=exclude_geometry)
# End validate_fields function


def exclude_special(element: ELEMENT, fields: list[Field],
                    exclude_primary: bool = True,
                    exclude_geometry: bool = True) -> list[Field]:
    """
    Exclude Special Fields
    """
    if exclude_primary:
        if key := element.primary_key_field:
            key_name = key.name.casefold()
            fields = [f for f in fields if f.name.casefold() != key_name]
    if exclude_geometry and isinstance(element, FeatureClass):
        if geom := element.geometry_column_name:
            geom_name = geom.casefold()
            fields = [f for f in fields if f.name.casefold() != geom_name]
    return fields
# End exclude_special function


def make_field_names(fields: FIELDS) -> str:
    """
    Make Field Names
    """
    return COMMA_SPACE.join(f.escaped_name for f in fields)
# End make_field_names function


def get_geometry_column_name(feature_class: FeatureClass,
                             include_geom_type: bool = False) -> str:
    """
    Get Geometry Column Name
    """
    name = feature_class.geometry_column_name
    if not include_geom_type:
        return name
    return f'{name} "[{feature_class.geometry_type}]"'
# End get_geometry_column_name function


def common_fields(a: ELEMENT, b: ELEMENT) -> FIELDS:
    """
    Fields in common between elements, check done based on name and type
    """
    a_fields = exclude_special(a, fields=a.fields)
    b_fields = exclude_special(b, fields=b.fields)
    # NOTE this means that we only have primary key and / or geometry fields
    if not a_fields or not b_fields:  # pragma: no cover
        return []
    a_lookup = _field_name_type(a_fields)
    b_lookup = _field_name_type(b_fields)
    shared = set(a_lookup).intersection(b_lookup)
    return [a_lookup[name, data_type] for name, data_type in shared]
# End common_fields function


def _field_name_type(fields: FIELDS) -> dict[tuple[str, str], Field]:
    """
    Translate Fields to a comparable lookup, rationalize data type
    """
    lookup = {}
    for field in fields:
        data_type = field.data_type.casefold()
        data_type = next((type_ for aliases, type_ in ALIAS_TYPE_LUT.items()
                          if data_type.startswith(aliases)), data_type)
        lookup[field.name.casefold(), data_type] = field
    return lookup
# End _field_name_type function


if __name__ == '__main__':  # pragma: no cover
    pass
