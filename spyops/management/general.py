# -*- coding: utf-8 -*-
"""
General Data Management
"""


from collections import defaultdict

from fudgeo import Table

from spyops.environment import OutputMOption, OutputZOption, Setting
from spyops.environment.context import Swap
from spyops.geometry.compare import compare_feature_geometry
from spyops.query.management.general import (
    QueryFindIdenticalFeatureClass, QueryFindIdenticalTable)
from spyops.shared.keywords import FIELDS_ARG, M_TOLERANCE, SOURCE, Z_TOLERANCE
from spyops.shared.element import copy_element
from spyops.shared.hint import (
    ELEMENT, ELEMENTS, FIELDS, FIELD_NAMES, M_TOL, XY_TOL, Z_TOL)
from spyops.validation import (
    validate_element, validate_elements, validate_field,
    validate_overwrite_source, validate_result, validate_source_element,
    validate_target_element, validate_tolerance, validate_xy_tolerance)


__all__ = ['copy', 'delete', 'rename', 'find_identical']


@validate_result()
@validate_element(SOURCE, has_content=False)
@validate_target_element()
@validate_overwrite_source()
def copy(source: ELEMENT, target: ELEMENT, *,
         where_clause: str = '') -> ELEMENT:
    """
    Copy Table or Feature Class

    Copies a source table to a target table or source feature class
    to a target feature class.  This function only honors the
    workspace-related analysis settings.
    """
    with (Swap(Setting.OUTPUT_COORDINATE_SYSTEM, None),
          Swap(Setting.GEOGRAPHIC_TRANSFORMATIONS, []),
          Swap(Setting.EXTENT, None), Swap(Setting.Z_VALUE, None),
          Swap(Setting.OUTPUT_M_OPTION, OutputMOption.SAME),
          Swap(Setting.OUTPUT_Z_OPTION, OutputZOption.SAME)):
        element = copy_element(source, target=target, where_clause=where_clause)
    return element
# End copy function


@validate_elements(SOURCE, has_content=False)
def delete(source: ELEMENT | ELEMENTS) -> bool:
    """
    Delete Table(s) and/or Feature Class(es)
    """
    if not source:
        return False
    # noinspection PyTypeChecker
    for element in source:
        element.drop()
    return True
# End delete function


@validate_result()
@validate_element(SOURCE, has_content=False)
def rename(source: ELEMENT, name: str) -> ELEMENT:
    """
    Rename Table or Feature Class
    """
    source.rename(name)
    # noinspection PyTypeChecker
    return source.geopackage[name]
# End rename function


@validate_result()
@validate_source_element()
@validate_target_element()
@validate_field(FIELDS_ARG, element_name=SOURCE)
@validate_xy_tolerance()
@validate_tolerance(Z_TOLERANCE)
@validate_tolerance(M_TOLERANCE)
@validate_overwrite_source()
def find_identical(source: ELEMENT, target: Table,
                   fields: FIELDS | FIELD_NAMES, include_geometry: bool = False,
                   *, xy_tolerance: XY_TOL = None, z_tolerance: Z_TOL = None,
                   m_tolerance: M_TOL = None) -> Table:
    """
    Find Identical

    Find Identical rows / features in a Table / Feature Class based on selected
    field names. Use XY, Z, and M tolerances to find geometries that are not
    quite but almost identical.

    The target table contains ORIG_FID and REPEAT_FID columns where the ORIG_FID
    is the original identifier and the REPEAT_FID is the identifier of one or
    more identical rows / features. Only the first repeated identifier is
    included in the ORIG_FID column along with its partner repeats.

    The target table does not include identifiers for rows / features that do
    not have repeats.
    """
    if isinstance(source, Table):
        cls = QueryFindIdenticalTable
    else:
        cls = QueryFindIdenticalFeatureClass
    # noinspection PyTypeChecker
    query = cls(source, target=target, fields=fields,
                include_geometry=include_geometry,
                xy_tolerance=xy_tolerance, z_tolerance=z_tolerance,
                m_tolerance=m_tolerance)
    records = []
    insert = query.insert
    select = query.select
    repeats = query.repeats
    has_z, has_m = query.has_zm
    groups = defaultdict(list)
    with (query.source.geopackage.connection as cin,
          query.target.geopackage.connection as cout):
        cursor = cin.execute(repeats)
        data = cursor.fetchall()
        for fid, group_id in data:
            groups[group_id].append(fid)
        if not select:
            for values in groups.values():
                first, *others = values
                records.extend([(first, other) for other in others])
            cout.executemany(insert, records)
            records.clear()
            return query.target
        for group_id in groups:
            cursor = cin.execute(select, (group_id,))
            features = cursor.fetchall()
            results = compare_feature_geometry(
                features, has_z=has_z, has_m=has_m, xy_tolerance=xy_tolerance,
                z_tolerance=z_tolerance, m_tolerance=m_tolerance)
            records.extend(results)
        cout.executemany(insert, records)
        records.clear()
    return query.target
# End find_identical function


if __name__ == '__main__':  # pragma: no cover
    pass
