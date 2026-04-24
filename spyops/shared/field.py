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


ALIAS_TYPE_LUT: dict[tuple[str, ...], str] = {
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


VALUE: Field = Field('VALUE', data_type=FieldType.real)
ORIG_FID: Field = Field(
    'ORIG_FID', data_type=FieldType.integer,
    alias='Original Feature Identifier')
ORIG_SEQ: Field = Field(
    'ORIG_SEQ', data_type=FieldType.integer,
    alias='Original Sequence Number')
MBG_WIDTH: Field = Field(
    'MBG_WIDTH', data_type=FieldType.real,
    alias='Width of Minimum Bounding Geometry')
MBG_LENGTH: Field = Field(
    'MBG_LENGTH', data_type=FieldType.real,
    alias='Length of Minimum Bounding Geometry')
MBG_ORIENTATION: Field = Field(
    'MBG_ORIENTATION', data_type=FieldType.real,
    alias='Orientation of Minimum Bounding Geometry')
REASON: Field = Field(
    'REASON', data_type=FieldType.text, alias='Geometry Check Reason')
POINT_X: Field = Field(
    'POINT_X', data_type=FieldType.real, alias='X Coordinate')
POINT_Y: Field = Field(
    'POINT_Y', data_type=FieldType.real, alias='Y Coordinate')
POINT_Z: Field = Field(
    'POINT_Z', data_type=FieldType.real, alias='Z Coordinate')
POINT_M: Field = Field(
    'POINT_M', data_type=FieldType.real, alias='M Coordinate')

GNSS_POSITION_SOURCE_TYPE_FIELD: Field = Field(
    'GNSS_POSITIONSOURCETYPE', data_type=FieldType.text,
    alias='Position Source Type')
GNSS_FIX_TYPE_FIELD: Field = Field(
    'GNSS_FIXTYPE', data_type=FieldType.text, alias='Fix Type')
GNSS_NUM_SATS_FIELD: Field = Field(
    'GNSS_NUMSATS', data_type=FieldType.integer, alias='Number of Satellites')
GNSS_WORST_FIX_TYPE_FIELD: Field = Field(
    'GNSS_WORST_FIXTYPE', data_type=FieldType.text, alias='Worst Fix Type')


GNSS_COMMON_FIELDS: FIELDS = (
    GNSS_POSITION_SOURCE_TYPE_FIELD,
    Field('GNSS_RECEIVER', data_type=FieldType.text, alias='Receiver Name'),
    Field('GNSS_LATITUDE', data_type=FieldType.real, alias='Latitude'),
    Field('GNSS_LONGITUDE', data_type=FieldType.real, alias='Longitude'),
    Field('GNSS_ALTITUDE', data_type=FieldType.real, alias='Altitude'),
    Field('GNSS_H_RMS', data_type=FieldType.real,
          alias='Horizontal Accuracy (m)'),
    Field('GNSS_V_RMS', data_type=FieldType.real,
          alias='Vertical Accuracy (m)'),
    Field('GNSS_FIXDATETIME', data_type=FieldType.datetime, alias='Fix Time'),
    GNSS_FIX_TYPE_FIELD,
    Field('GNSS_CORRECTIONAGE', data_type=FieldType.real,
          alias='Correction Age'),
    Field('GNSS_STATIONID', data_type=FieldType.integer, alias='Station ID'),
    GNSS_NUM_SATS_FIELD,
    Field('GNSS_PDOP', data_type=FieldType.real, alias='PDOP'),
    Field('GNSS_HDOP', data_type=FieldType.real, alias='HDOP'),
    Field('GNSS_VDOP', data_type=FieldType.real, alias='VDOP'),
    Field('GNSS_DIRECTION', data_type=FieldType.real,
          alias='Direction of travel (°)'),
    Field('GNSS_SPEED', data_type=FieldType.real, alias='Speed (km/h)'),
    Field('SNSR_AZIMUTH', data_type=FieldType.real,
          alias='Compass reading (°)'),
    Field('GNSS_AVG_H_RMS', data_type=FieldType.real,
          alias='Average Horizontal Accuracy (m)'),
    Field('GNSS_AVG_V_RMS', data_type=FieldType.real,
          alias='Average Vertical Accuracy (m)'),
    Field('GNSS_AVG_POSITIONS', data_type=FieldType.integer,
          alias='Averaged Positions'),
    Field('GNSS_H_STDDEV', data_type=FieldType.real,
          alias='Standard Deviation (m)'),
)
GNSS_POLY_LINE_FIELDS: FIELDS = (
    Field('GNSS_AVG_H_RMS', data_type=FieldType.real,
          alias='Average Horizontal Accuracy (m)'),
    Field('GNSS_AVG_V_RMS', data_type=FieldType.real,
          alias='Average Vertical Accuracy (m)'),
    Field('GNSS_WORST_H_RMS', data_type=FieldType.real,
          alias='Worst Horizontal Accuracy (m)'),
    Field('GNSS_WORST_V_RMS', data_type=FieldType.real,
          alias='Worst Vertical Accuracy (m)'),
    GNSS_WORST_FIX_TYPE_FIELD,
    Field('GNSS_MANUAL_LOCATIONS', data_type=FieldType.integer,
          alias='Number of Manual Locations'),
)


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
        # noinspection PyTypeChecker
        fields = fields,
    for f in fields:
        if not isinstance(f, (Field, str)):
            continue
        # noinspection PyUnresolvedReferences
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


def add_orig_fid(feature_class: FeatureClass) -> FIELDS:
    """
    Add Original FID
    """
    key = ORIG_FID.name.casefold()
    fields = list(validate_fields(feature_class, fields=feature_class.fields))
    names = [f.name.casefold() for f in fields]
    if key not in names:
        return ORIG_FID, *fields
    index = names.index(key)
    field, = make_unique_fields([ORIG_FID, *fields], others=[fields[index]])
    fields[index] = field
    return ORIG_FID, *fields
# End add_orig_fid function


def add_key_fields(fields: list[Field], key_fields: FIELDS) -> FIELDS:
    """
    Add Key Fields
    """
    keys = [f.name.casefold() for f in key_fields]
    names = [f.name.casefold() for f in fields]
    if not any(key in names for key in keys):
        return *key_fields, *fields
    for key, fld in zip(keys, key_fields):
        if key not in names:
            continue
        index = names.index(key)
        fld, = make_unique_fields([fld, *fields], others=[fields[index]])
        fields[index] = fld
    return *key_fields, *fields
# End add_key_fields function


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
