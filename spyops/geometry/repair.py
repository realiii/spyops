# -*- coding: utf-8 -*-
"""
Repair Geometry
"""


from typing import Callable, Optional, TYPE_CHECKING, TypeAlias, Union

from fudgeo import FeatureClass
from fudgeo.constant import FETCH_SIZE
from fudgeo.enumeration import ShapeType
from numpy import array
from shapely import get_num_points
from shapely.constructive import make_valid
from shapely.predicates import is_empty, is_valid, is_valid_reason

from spyops.geometry.constant import (
    REASON_INVALID_COORDINATE, REASON_TOO_FEW_POINTS)
from spyops.geometry.util import to_shapely
from spyops.geometry.wa import make_valid_structure


if TYPE_CHECKING:  # pragma: no cover
    from numpy import ndarray
    from shapely.geometry.base import BaseGeometry, BaseMultipartGeometry


DELETES: TypeAlias = list[int]
EMPTIES: TypeAlias = list[int]
UPDATES: TypeAlias = list[tuple[
    Optional[Union['BaseGeometry', 'BaseMultipartGeometry']], int]]


def repair_feature_class_geometry(source: 'FeatureClass') \
        -> tuple[DELETES, UPDATES, EMPTIES]:
    """
    Repair Feature Class Geometry, addresses geometry issues but not the
    feature class extent.

    The deletes list is for the identifiers of features that are initially
    empty and should be dropped, the empties list is for identifiers of
    features that have become empty during the process of making valid, and
    the updates list is for features that have been made valid and must be
    updated in the feature class.

    When the option to drop empty features is True the empties and deletes
    lists are combined, when False fudgeo empty geometries are generated for
    each identifier in the empties list and combined used in conjunction with
    the updates list.
    """
    updates = []
    deletes = []
    empties = []
    has_m = source.has_m
    shape_type = source.shape_type
    kwargs = dict(deletes=deletes, updates=updates,
                  empties=empties, has_m=has_m)
    repairer = GEOMETRY_REPAIRER[shape_type]
    cursor = source.select(include_primary=True)
    while features := cursor.fetchmany(FETCH_SIZE):
        features, geometries = to_shapely(
            features, transformer=None, on_invalid='fix')
        ids = array([fid for _, fid in features], dtype=int)
        repairer(geometries, ids=ids, **kwargs)
    return deletes, updates, empties
# End repair_feature_class_geometry function


def _make_valid(geoms: 'ndarray') -> 'ndarray':
    """
    Small wrapper around make_valid to support arrays -- for use when there
    are no measure values on the geometries.
    """
    return make_valid(geoms, method='structure', keep_collapsed=False)
# End _make_valid function


def _make_none_mask(values: 'ndarray') -> 'ndarray':
    """
    Create a mask of None values for the given array.
    """
    # NOTE this is the way
    return values == None
# End _make_none_mask function


def _filter_empty_none(geoms: 'ndarray', *, ids: 'ndarray', deletes: DELETES,
                       empties: EMPTIES) -> tuple['ndarray', 'ndarray']:
    """
    Filter Empty and None, tracking in the relevant lists.
    """
    mask_none = _make_none_mask(geoms)
    empties.extend(ids[mask_none])
    mask_empty = is_empty(geoms)
    deletes.extend(ids[mask_empty])
    mask = mask_none | mask_empty
    return geoms[~mask], ids[~mask]
# End _filter_empty_none function


def _track_updates_empties(geoms: 'ndarray', *, ids: 'ndarray',
                           updates: UPDATES, empties: DELETES) -> None:
    """
    Track Updates and Empties
    """
    mask = is_empty(geoms) | _make_none_mask(geoms)
    empties.extend(ids[mask])
    updates.extend(list(zip(geoms[~mask], ids[~mask])))
# End _track_updates_empties function


def _repair_points(geoms: 'ndarray', ids: 'ndarray', *,
                   deletes: DELETES, **kwargs) -> None:
    """
    Repair Points, build up empty points as features to drop
    """
    deletes.extend(ids[~is_valid(geoms) | is_empty(geoms)])
# End _repair_points function


def _repair_multi_points(geoms: 'ndarray', ids: 'ndarray', *, deletes: DELETES,
                         updates: UPDATES, empties: EMPTIES, has_m: bool,
                         **kwargs) -> None:
    """
    Repair Multi Points, removes empty points
    """
    geoms, ids = _filter_empty_none(geoms, ids=ids, deletes=deletes, empties=empties)
    if not has_m:
        valid = _make_valid(geoms)
        _track_updates_empties(valid, ids=ids, updates=updates, empties=empties)
    else:
        for fid, geom in zip(ids, geoms):
            geom = make_valid_structure(geom)
            if geom is None or geom.is_empty:
                empties.append(fid)
            else:
                updates.append((geom, fid))
# End _repair_multi_points function


def _repair_linestrings(geoms: 'ndarray', ids: 'ndarray', *, deletes: DELETES,
                        updates: UPDATES, empties: EMPTIES, has_m: bool,
                        **kwargs) -> None:
    """
    Repair LineStrings, removes empty points and changes lines with incorrect
    line count to empty lines.  Coincident points are left as is, this is
    mostly to ensure that vertical lines (or portions of vertical lines) are
    kept untouched.
    """
    geoms, ids = _filter_empty_none(
        geoms, ids=ids, deletes=deletes, empties=empties)
    reasons = is_valid_reason(geoms)
    required = 2
    if not has_m:
        indexes = [i for i, reason in enumerate(reasons)
                   if reason and reason.startswith(REASON_INVALID_COORDINATE)]
        valid = _make_valid(geoms[indexes])
        _track_updates_empties(
            valid, ids=ids[indexes], updates=updates, empties=empties)
        indexes = [i for i, reason in enumerate(reasons)
                   if reason and reason.startswith(REASON_TOO_FEW_POINTS)]
        geoms = geoms[indexes]
        geoms[get_num_points(geoms) < required] = None
        _track_updates_empties(
            geoms, ids=ids[indexes], updates=updates, empties=empties)
    else:
        for fid, geom, reason in zip(ids, geoms, reasons):
            if reason.startswith(REASON_INVALID_COORDINATE):
                geom = make_valid_structure(geom)
            elif reason.startswith(REASON_TOO_FEW_POINTS):
                if get_num_points(geom) < required:
                    geom = None
            if geom is None or geom.is_empty:
                empties.append(fid)
            else:
                updates.append((geom, fid))
# End _repair_linestrings function


def _repair_multi_linestrings(geoms: 'ndarray', ids: 'ndarray', *,
                              deletes: DELETES, updates: UPDATES,
                              empties: EMPTIES, **kwargs) -> None:
    """
    Repair Multi LineStrings,
    """
    pass
# End _repair_multi_linestrings function


GEOMETRY_REPAIRER: dict[str, Callable] = {
    ShapeType.point: _repair_points,
    ShapeType.multi_point: _repair_multi_points,
    ShapeType.linestring: _repair_linestrings,
    ShapeType.multi_linestring: _repair_multi_linestrings,
}

if __name__ == '__main__':  # pragma: no cover
    pass
