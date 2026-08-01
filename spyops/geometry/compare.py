# -*- coding: utf-8 -*-
"""
Compare Features
"""


from typing import TYPE_CHECKING

from numpy import allclose, array
from shapely.constructive import normalize
from shapely.coordinates import get_coordinates
from shapely.predicates import equals_exact

from spyops.geometry.util import filter_features, find_slice_indexes, to_shapely
from spyops.geometry.wa import make_valid_structure
from spyops.shared.hint import M_TOL, XY_TOL, Z_TOL


if TYPE_CHECKING:  # pragma: no cover
    from numpy import ndarray
    from shapely.geometry.base import BaseGeometry


def compare_feature_geometry(features: list[tuple], *,
                             has_z: bool = False, has_m: bool = False,
                             xy_tolerance: XY_TOL = None,
                             z_tolerance: Z_TOL = None,
                             m_tolerance: M_TOL = None) -> list:
    """
    Compare Feature Geometry, empty features are filtered out and not considered
    in the comparison.
    """
    records = []
    if not (features := filter_features(features)):
        return records
    features, geometries = to_shapely(
        features, transformer=lambda x: x, on_invalid='ignore')
    ids = array([i for _, i in features], dtype=int)
    geoms = normalize([make_valid_structure(geom) for geom in geometries])
    grp_geom, grp_id = _compare_2d(geoms, ids=ids, xy_tolerance=xy_tolerance)
    if not grp_id:
        return records
    if not has_z and not has_m:
        for id_, ids in grp_id.items():
            records.extend([(id_, i) for i in ids])
        return records
    return _compare_zm(
        grp_geom, grp_id, z_tolerance=z_tolerance, m_tolerance=m_tolerance)
# End compare_feature_geometry function


def _compare_2d(geoms: 'ndarray', ids: 'ndarray', xy_tolerance: XY_TOL) \
        -> tuple[dict[int, list['BaseGeometry']], dict[int, list[int]]]:
    """
    Compare Geometry based on 2D coordinates, geometry must be normalized.
    """
    geometries = {}
    identifiers = {}
    xy_tol = xy_tolerance or 0.
    while len(geoms) > 1:
        # NOTE avoid unpacking to keep ids and geoms as arrays
        id_, ids = ids[0], ids[1:]
        geom, geoms = geoms[0], geoms[1:]
        matches = equals_exact(geom, geoms, tolerance=xy_tol)
        if not matches.any():
            continue
        identifiers[id_] = ids[matches]
        geometries[id_] = geom, *geoms[matches]
        ids = ids[~matches]
        geoms = geoms[~matches]
    return geometries, identifiers
# End _compare_2d function


def _compare_zm(grouped_geom: dict[int, list['BaseGeometry']],
                grouped_ids: dict[int, list[int]], *, z_tolerance: Z_TOL,
                m_tolerance: M_TOL) -> list[tuple[int, int]]:
    """
    Compare Geometry based on Z and M coordinates
    """
    records = []
    z_tol = z_tolerance or 0.
    m_tol = m_tolerance or 0.
    for id_, ids in grouped_ids.items():
        geoms = grouped_geom[id_]
        coordinates, indexes = get_coordinates(
            geoms, include_z=True, include_m=True, return_index=True)
        indexes = find_slice_indexes(indexes)
        first, second, *_ = indexes
        coords = coordinates[first:second]
        zs = coords[:, 2]
        ms = coords[:, 3]
        for oid, begin, end in zip(ids, indexes[1:-1], indexes[2:]):
            coords = coordinates[begin:end]
            z_match = allclose(zs, coords[:, 2], rtol=z_tol, equal_nan=True)
            m_match = allclose(ms, coords[:, 3], rtol=m_tol, equal_nan=True)
            if not (z_match and m_match):
                continue
            records.append((id_, oid))
    return records
# End _compare_zm function


if __name__ == '__main__':  # pragma: no cover
    pass
