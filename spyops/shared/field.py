# -*- coding: utf-8 -*-
"""
Field
"""


from fudgeo import FeatureClass, Field
from fudgeo.constant import COMMA_SPACE
from fudgeo.enumeration import ShapeType, FieldType

from spyops.shared.hint import ELEMENT, FIELDS, FIELD_NAMES, NAMES
from spyops.shared.util import make_unique_name


GEOM_TYPE_POINTS: NAMES = ShapeType.point, ShapeType.multi_point
GEOM_TYPE_LINES: NAMES = ShapeType.linestring, ShapeType.multi_linestring
GEOM_TYPE_POLYGONS: NAMES = ShapeType.polygon, ShapeType.multi_polygon
GEOM_TYPE_MULTI: NAMES = (ShapeType.multi_point,
                          ShapeType.multi_linestring,
                          ShapeType.multi_polygon)


ALIAS_TYPE_LUT: dict[NAMES, str] = {
    (FieldType.boolean.casefold(),): FieldType.boolean,
    (FieldType.blob.casefold(),): FieldType.blob,
    (FieldType.tinyint.casefold(),): FieldType.tinyint,
    (FieldType.smallint.casefold(),): FieldType.smallint,
    (FieldType.mediumint.casefold(),): FieldType.mediumint,
    ('char', 'varchar', 'tinytext', FieldType.text.casefold(), 'mediumtext',
     'longtext', 'nchar', 'nvarchar', 'clob'): FieldType.text,
    ('numeric', 'decimal', FieldType.real.casefold()): FieldType.real,
    (FieldType.double.casefold(), 'double precision'): FieldType.double,
    (FieldType.float.casefold(),): FieldType.float,
    (FieldType.date.casefold(),): FieldType.date,
    (FieldType.datetime.casefold(),): FieldType.datetime,
    ('time', FieldType.timestamp.casefold()): FieldType.timestamp,
    ('int', FieldType.integer.casefold(), 'bigint', 'int2',
     'int4', 'int8'): FieldType.integer,
}
TYPE_ALIAS_LUT: dict[str, NAMES] = {
    v: k for k, v in ALIAS_TYPE_LUT.items()}


DATES: NAMES = FieldType.date, FieldType.datetime, FieldType.timestamp
INTEGERS: NAMES = (FieldType.tinyint, FieldType.smallint,
                   FieldType.mediumint, FieldType.integer)
REALS: NAMES = FieldType.float, FieldType.double, FieldType.real
TEXTS: NAMES = FieldType.text,
NUMBERS: NAMES = (*INTEGERS, *REALS)
TEXT_AND_INTEGERS: NAMES = (*TEXTS, *INTEGERS)
TEXT_AND_NUMBERS: NAMES = (*TEXTS, *NUMBERS)
TEXT_AND_REALS: NAMES = (*TEXTS, *REALS)


ORIG_FID: Field = Field('ORIG_FID', data_type=FieldType.integer)


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


def clone_field(field: Field, name: str, allow_null: bool = False) -> Field:
    """
    Clone Field
    """
    if allow_null:
        is_nullable = True
    else:
        is_nullable = field.is_nullable
    return Field(name=name, data_type=field.data_type, size=field.size,
                 is_nullable=is_nullable, default=field.default,
                 alias=field.alias, comment=field.comment)
# End clone_field method


def make_unique_fields(base: FIELDS, others: FIELDS) -> FIELDS:
    """
    Make Unique Fields
    """
    names = {f.name.casefold() for f in base}
    return [clone_field(f, name=make_unique_name(f.name, names=names))
            for f in others]
# End make_unique_fields function


if __name__ == '__main__':  # pragma: no cover
    pass
