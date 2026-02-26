# -*- coding: utf-8 -*-
"""
Invalid Checks
"""


from collections import defaultdict
from typing import TYPE_CHECKING, TypeAlias, Union

from bottleneck import allnan, anynan
from fudgeo.constant import FETCH_SIZE
from fudgeo.enumeration import ShapeType
from fudgeo.util import get_extent
from numpy import array, isclose, isfinite, isnan
from shapely import LineString as ShapelyLineString, Polygon as ShapelyPolygon
from shapely.coordinates import get_coordinates
from shapely.io import from_wkb
from shapely.predicates import is_ccw, is_closed, is_valid

from spyops.geometry.util import find_slice_indexes
from spyops.shared.enumeration import GeometryCheck


if TYPE_CHECKING:  # pragma: no cover
    from fudgeo import FeatureClass
    from fudgeo.geometry import (
        LineString, LineStringM, LineStringZ, LineStringZM, MultiLineString,
        MultiLineStringM, MultiLineStringZ, MultiLineStringZM, MultiPoint,
        MultiPointM, MultiPointZ, MultiPointZM, MultiPolygon, MultiPolygonM,
        MultiPolygonZ, MultiPolygonZM, PointM, PointZ, PointZM, Polygon,
        PolygonM, PolygonZ, PolygonZM)
    from fudgeo.geometry.base import AbstractGeometry


RECORDS: TypeAlias = list[tuple[int, str]]
FEATURES: TypeAlias = list[tuple['AbstractGeometry', int]]


def check_feature_class_geometry(source: 'FeatureClass',
                                 options: GeometryCheck) -> RECORDS:
    """
    Check Feature Class Geometry
    """
    records = []
    has_z = source.has_z
    has_m = source.has_m
    shape_type = source.shape_type
    cursor = source.select(include_primary=True)
    kwargs = dict(options=options, shape_type=shape_type,
                  records=records, has_z=has_z, has_m=has_m)
    _check_extent(source, **kwargs)
    while features := cursor.fetchmany(FETCH_SIZE):
        if not (features := _check_empty_feature(features, **kwargs)):
            continue
        _check_empty_part(features, **kwargs)
        _check_empty_ring(features, **kwargs)
        _check_empty_point(features, **kwargs)
        _check_nan_z(features, **kwargs)
        _check_nan_m(features, **kwargs)
        _check_coordinates(features, **kwargs)
        _check_line(features, **kwargs)
        _check_polygon(features, **kwargs)
    return records
# End check_feature_class_geometry function


def _check_extent(source: 'FeatureClass', *, options: GeometryCheck,
                  records: RECORDS, **kwargs) -> None:
    """
    Check Extent, report error if not set (all nan) or if the current extent
    is out of range by 0.000012% (same percentage as rtree spatial index)
    """
    check = GeometryCheck.EXTENT
    if check not in options:
        return
    record = (-1, _get_name(check))
    table_extent = source.extent
    if not isfinite(table_extent).all():
        records.append(record)
        return
    geometry_extent = get_extent(source)
    if not isclose(table_extent, geometry_extent, rtol=1.2e-7).all():
        records.append(record)
# End _check_extent function


def _check_empty_feature(features: FEATURES, *, options: GeometryCheck,
                         records: RECORDS, **kwargs) -> FEATURES:
    """
    Check Empty Features and filter out empty geometries
    """
    check = GeometryCheck.EMPTY
    validity = [geom.is_empty for geom, _ in features]
    if check in options:
        name = _get_name(check)
        records.extend([(fid, name) for (_, fid), is_empty in
                        zip(features, validity) if is_empty])
    return [f for f, is_empty in zip(features, validity) if not is_empty]
# End _check_empty_feature function


def _check_empty_part(features: FEATURES, *, options: GeometryCheck,
                      shape_type: str, records: RECORDS, **kwargs) -> None:
    """
    Check Empty Part, applies to MultiLineString and MultiPolygon
    """
    check = GeometryCheck.EMPTY_PART
    if check not in options:
        return
    ids = []
    if shape_type == ShapeType.multi_linestring:
        mls: 'MultiLineString'
        ids = [fid for mls, fid in features
               if any(line.is_empty for line in mls)]
    elif shape_type == ShapeType.multi_polygon:
        mup: 'MultiPolygon'
        ids = [fid for mup, fid in features
               if any(poly.is_empty for poly in mup)]
    name = _get_name(check)
    records.extend([(fid, name) for fid in ids])
# End _check_empty_part function


def _check_empty_ring(features: FEATURES, *, options: GeometryCheck,
                      shape_type: str, records: RECORDS, **kwargs) -> None:
    """
    Check Empty Ring, applies to Polygon and MultiPolygon only
    """
    check = GeometryCheck.EMPTY_RING
    if check not in options or shape_type not in (
            ShapeType.polygon, ShapeType.multi_polygon):
        return
    ids = []
    if shape_type == ShapeType.polygon:
        poly: 'Polygon'
        ids = [fid for poly, fid in features
               if any(ring.is_empty for ring in poly)]
    elif shape_type == ShapeType.multi_polygon:
        mup: 'MultiPolygon'
        ids = [fid for mup, fid in features
               if any(any(ring.is_empty for ring in poly) for poly in mup)]
    name = _get_name(check)
    records.extend([(fid, name) for fid in ids])
# End _check_empty_ring function


def _check_empty_point(features: FEATURES, *, options: GeometryCheck,
                       shape_type: str, records: RECORDS, **kwargs) -> None:
    """
    Check Empty Point
    """
    check = GeometryCheck.EMPTY_POINT
    # NOTE empty point checks for point addressed by _check_empty_feature
    if check not in options or shape_type == ShapeType.point:
        return
    ids = []
    if shape_type in (ShapeType.multi_point, ShapeType.linestring):
        mpl: Union['MultiPoint', 'LineString']
        ids = [fid for mpl, fid in features
               if allnan(mpl.coordinates, axis=1).any()]
    elif shape_type == ShapeType.polygon:
        poly: 'Polygon'
        ids = [fid for poly, fid in features
               if any(allnan(ring.coordinates, axis=1).any() for ring in poly)]
    elif shape_type == ShapeType.multi_linestring:
        mls: 'MultiLineString'
        for mls, fid in features:
            for line in mls:
                if allnan(line.coordinates, axis=1).any():
                    ids.append(fid)
                    break
    elif shape_type == ShapeType.multi_polygon:
        mup: 'MultiPolygon'
        for mup, fid in features:
            for poly in mup:
                if any(allnan(ring.coordinates, axis=1).any() for ring in poly):
                    ids.append(fid)
                    break
    name = _get_name(check)
    records.extend([(fid, name) for fid in ids])
# End _check_empty_point function


def _check_polygon(features: FEATURES, *, options: GeometryCheck,
                   shape_type: str, records: RECORDS, **kwargs) -> None:
    """
    Check Polygon Orientation, Closed Rings, and Self Intersection
    """
    checks = (GeometryCheck.ORIENTATION, GeometryCheck.UNCLOSED,
              GeometryCheck.SELF_INTERSECTION, GeometryCheck.OUTSIDE_RING,
              GeometryCheck.OVERLAP_RING, GeometryCheck.POINT_COUNT)
    if (not any(check in options for check in checks) or
            shape_type not in (ShapeType.polygon, ShapeType.multi_polygon)):
        return
    validations = {}
    if shape_type == ShapeType.polygon:
        poly: 'Polygon'
        for poly, fid in features:
            state = _get_polygon_state(poly)
            if True in state:
                validations[fid] = state
    elif shape_type == ShapeType.multi_polygon:
        mup: 'MultiPolygon'
        for mup, fid in features:
            for poly in mup:
                state = _get_polygon_state(poly)
                if True in state:
                    validations[fid] = state
                    break
    names = [_get_name(check) for check in checks]
    checks = (GeometryCheck.ORIENTATION in options,
              GeometryCheck.UNCLOSED in options,
              GeometryCheck.SELF_INTERSECTION in options,
              GeometryCheck.OUTSIDE_RING in options,
              GeometryCheck.OVERLAP_RING in options,
              GeometryCheck.POINT_COUNT in options)
    for fid, validity in validations.items():
        for use_check, has_error, name in zip(checks, validity, names):
            if not use_check or not has_error:
                continue
            records.append((fid, name))
# End _check_polygon function


def _get_polygon_state(polygon: 'Polygon') \
        -> tuple[bool, bool, bool, bool, bool, bool]:
    """
    Find Counter-Clockwise (exterior) and Clockwise (interior) state, return
    a single boolean value indicating if the polygon is ok.  Check if the
    rings are closed.  Check for self intersections.  Check for point count.
    Check for overlapping interior rings.  Check for interior rings outside
    the exterior ring.
    """
    # NOTE as a line need 3 points at least for polygon to be created
    count = 3
    coords = [ring.coordinates[:, :2] for ring in polygon]
    has_bad_point_count = any(len(coord) < count for coord in coords)
    if not (coords := [coord for coord in coords if len(coord) >= count]):
        return False, False, False, False, False, has_bad_point_count
    lines = [ShapelyLineString(coord) for coord in coords]
    # NOTE purposely perform is_closed on lines
    has_unclosed = not is_closed(lines).all()
    # NOTE shapely documentation says is_simple will be True for Polygons and
    #  suggests using is_valid instead, hopefully this finds self intersections
    polys = [ShapelyPolygon(line) for line in lines]
    has_self_intersection = not is_valid(polys).all()
    ccw = is_ccw(lines)
    if len(polys) <= 1:
        has_bad_orientation = not ccw.all()
        has_outside_ring = has_overlap_ring = False
    else:
        has_bad_orientation = not ccw[0] or ccw[1:].any()
        exterior, *interiors = polys
        has_outside_ring = not exterior.contains(interiors).all()
        has_overlap_ring = False
        if len(interiors) > 1:
            _, *interiors = lines
            for i, boundary in enumerate(interiors[:-1], 1):
                if boundary.intersects(interiors[i:]).any():
                    has_overlap_ring = True
                    break
    return (has_bad_orientation, has_unclosed, has_self_intersection,
            has_outside_ring, has_overlap_ring, has_bad_point_count)
# End _get_polygon_state function


def _check_line(features: FEATURES, *, options: GeometryCheck, shape_type: str,
                records: RECORDS, **kwargs) -> None:
    """
    Check Line
    """
    check = GeometryCheck.POINT_COUNT
    if check not in options or shape_type not in (
            ShapeType.linestring, ShapeType.multi_linestring):
        return
    ids = []
    count = 2
    if shape_type == ShapeType.linestring:
        line: 'LineString'
        for line, fid in features:
            if len(line.coordinates) < count:
                ids.append(fid)
    elif shape_type == ShapeType.multi_linestring:
        mls: 'MultiLineString'
        for mls, fid in features:
            for line in mls:
                if len(line.coordinates) < count:
                    ids.append(fid)
                    break
    name = _get_name(check)
    records.extend([(fid, name) for fid in ids])
# End _check_line function


def _check_nan_z(features: FEATURES, *, options: GeometryCheck, shape_type: str,
                 has_z: bool, records: RECORDS, **kwargs) -> None:
    """
    Check NaN Z
    """
    check = GeometryCheck.NAN_Z
    if check not in options or not has_z:
        return
    ids = []
    idx = 2
    if shape_type == ShapeType.point:
        pt: PointZ | PointZM
        ids, zs = zip(*[(fid, pt.z) for pt, fid in features])
        ids = array(ids, dtype=int)
        ids = ids[isnan(zs)]
    elif shape_type in (ShapeType.multi_point, ShapeType.linestring):
        mpl: Union['MultiPointZ', 'MultiPointZM', 'LineStringZ', 'LineStringZM']
        ids = [fid for mpl, fid in features
               if anynan(mpl.coordinates[:, idx])]
    elif shape_type == ShapeType.multi_linestring:
        mls: Union['MultiLineStringZ', 'MultiLineStringZM']
        ids = [fid for mls, fid in features
               if any(anynan(line.coordinates[:, idx]) for line in mls)]
    elif shape_type == ShapeType.polygon:
        poly: Union['PolygonZ', 'PolygonZM']
        ids = [fid for poly, fid in features
               if any(anynan(ring.coordinates[:, idx]) for ring in poly)]
    elif shape_type == ShapeType.multi_polygon:
        mup: Union['MultiPolygonZ', 'MultiPolygonZM']
        ids = [fid for mup, fid in features
               if any(any(anynan(ring.coordinates[:, idx])
                          for ring in poly) for poly in mup)]
    name = _get_name(check)
    records.extend([(fid, name) for fid in ids])
# End _check_nan_z function


def _check_nan_m(features: FEATURES, *, options: GeometryCheck, shape_type: str,
                 has_z: bool, has_m: bool, records: RECORDS, **kwargs) -> None:
    """
    Check NaN M
    """
    check = GeometryCheck.NAN_M
    if check not in options or not has_m:
        return
    ids = []
    idx = 1 + has_z + has_m
    if shape_type == ShapeType.point:
        pt: Union['PointM', 'PointZM']
        ids, zs = zip(*[(fid, pt.m) for pt, fid in features])
        ids = ids[isnan(zs)]
    elif shape_type in (ShapeType.multi_point, ShapeType.linestring):
        mpl: Union['MultiPointM', 'MultiPointZM', 'LineStringM', 'LineStringZM']
        ids = [fid for mpl, fid in features
               if anynan(mpl.coordinates[:, idx])]
    elif shape_type == ShapeType.multi_linestring:
        mls: Union['MultiLineStringM', 'MultiLineStringZM']
        ids = [fid for mls, fid in features
               if any(anynan(line.coordinates[:, idx]) for line in mls)]
    elif shape_type == ShapeType.polygon:
        poly: Union['PolygonM', 'PolygonZM']
        ids = [fid for poly, fid in features
               if any(anynan(ring.coordinates[:, idx]) for ring in poly)]
    elif shape_type == ShapeType.multi_polygon:
        mup: Union['MultiPolygonM', 'MultiPolygonZM']
        ids = [fid for mup, fid in features
               if any(any(anynan(ring.coordinates[:, idx])
                          for ring in poly) for poly in mup)]
    name = _get_name(check)
    records.extend([(fid, name) for fid in ids])
# End _check_nan_m function


def _check_coordinates(features: FEATURES, *, options: GeometryCheck,
                       shape_type: str, has_z: bool, has_m: bool,
                       records: RECORDS, **kwargs) -> None:
    """
    Check Coordinates
    """
    checks = (GeometryCheck.REPEATED_XY, GeometryCheck.REPEATED_M,
              GeometryCheck.MISMATCH_Z, GeometryCheck.MISMATCH_M)
    if (not any(check in options for check in checks) or
            shape_type == ShapeType.point):
        return
    check_repeated_xy = GeometryCheck.REPEATED_XY in options
    check_repeated_m = GeometryCheck.REPEATED_M in options and has_m
    check_mismatch_z = GeometryCheck.MISMATCH_Z in options and has_z
    check_mismatch_m = GeometryCheck.MISMATCH_M in options and has_m
    wkb, fids = zip(*[(geom.wkb, fid) for geom, fid in features])
    geoms = from_wkb(wkb, on_invalid='ignore')
    if not (fids := [i for i, geom in zip(fids, geoms) if geom is not None]):
        return
    coords, indexes = get_coordinates(
        geoms, include_z=has_z, include_m=has_m, return_index=True)
    # NOTE round coordinates to 8 decimal places for grouping and comparison
    coords = coords.round(8)
    validations = {}
    index = 1 + has_z + has_m
    ids = find_slice_indexes(indexes)
    for fid, begin, end in zip(fids, ids[:-1], ids[1:]):
        repeated_xy = repeated_m = mismatch_z = mismatch_m = False
        grouped = defaultdict(list)
        for x, y, *values in coords[begin:end]:
            grouped[(x, y)].append(values)
        repetitions = {key: values for key, values in grouped.items()
                       if len(values) > 1}
        if check_repeated_xy:
            repeated_xy = bool(repetitions)
        if check_repeated_m:
            # NOTE use all coordinates, looking for any repeated m values
            #  within the feature independent of the xy grouping
            ms = coords[begin:end][:, index]
            ms = ms[isfinite(ms)]
            repeated_m = len(set(ms)) != len(ms)
        if check_mismatch_z:
            mismatch_z = _find_mismatch(repetitions, index=0)
        if check_mismatch_m:
            mismatch_z = _find_mismatch(repetitions, index=-1)
        if not any((repeated_xy, repeated_m, mismatch_z, mismatch_m)):
            continue
        validations[fid] = repeated_xy, repeated_m, mismatch_z, mismatch_m
    names = [_get_name(check) for check in checks]
    checks = (check_repeated_xy, check_repeated_m,
              check_mismatch_z, check_mismatch_m)
    for fid, validity in validations.items():
        for use_check, has_error, name in zip(checks, validity, names):
            if not use_check or not has_error:
                continue
            records.append((fid, name))
# End _check_coordinates function


def _find_mismatch(data: dict[tuple[float, float], list[tuple]],
                   index: int) -> bool:
    """
    Find Mismatch at the same xy
    """
    for values in data.values():
        vals = array([value[index] for value in values], dtype=float)
        vals = vals[isfinite(vals)]
        if len(set(vals)) != len(vals):
            return True
    return False
# End _find_mismatch function


def _get_name(value: GeometryCheck) -> str:
    """
    Get Name
    """
    return str(value.name)
# End _get_name function


if __name__ == '__main__':  # pragma: no cover
    pass
