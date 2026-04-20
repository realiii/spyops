# -*- coding: utf-8 -*-
"""
Line Segment
"""
from typing import Callable

from fudgeo.enumeration import ShapeType

from spyops.shared.hint import LINE, LINE_TYPE


def segment_linestrings(features: list[tuple], *, geom_cls: LINE_TYPE,
                        srs_id: int) -> list[tuple[LINE, int, int]]:
    """
    Segment from LineStrings
    """
    segments = []
    if not features:
        return segments
    for line, fid in features:
        if line.is_empty:
            continue
        coords = line.coordinates
        segments.extend(
            [(geom_cls([(begin, end)], srs_id=srs_id), fid, i)
             for i, (begin, end) in enumerate(zip(coords[:-1], coords[1:]), 1)])
    return segments
# End segment_linestrings function


def segment_multi_linestrings(features: list[tuple], *, geom_cls: LINE_TYPE,
                              srs_id: int) -> list[tuple[LINE, int, int]]:
    """
    Segment from MultiLineStrings
    """
    segments = []
    if not features:
        return segments
    for multi, fid in features:
        if multi.is_empty:
            continue
        counter = 1
        for line in multi:
            if line.is_empty:
                continue
            coords = line.coordinates
            lines = [(geom_cls([(begin, end)], srs_id=srs_id), fid, i)
                     for i, (begin, end) in enumerate(
                    zip(coords[:-1], coords[1:]), counter)]
            counter += len(lines)
            segments.extend(lines)
    return segments
# End segment_multi_linestrings function


def segment_polygons(features: list[tuple], *, geom_cls: LINE_TYPE,
                     srs_id: int) -> list[tuple[LINE, int, int]]:
    """
    Segment from Polygons
    """
    return segment_multi_linestrings(features, geom_cls=geom_cls, srs_id=srs_id)
# End segment_polygons function


def segment_multi_polygons(features: list[tuple], *, geom_cls: LINE_TYPE,
                           srs_id: int) -> list[tuple[LINE, int, int]]:
    """
    Segment from MultiPolygons
    """
    segments = []
    if not features:
        return segments
    for multi, fid in features:
        if multi.is_empty:
            continue
        counter = 1
        for poly in multi:
            if poly.is_empty:
                continue
            for ring in poly:
                if ring.is_empty:
                    continue
                coords = ring.coordinates
                lines = [(geom_cls([(begin, end)], srs_id=srs_id), fid, i)
                         for i, (begin, end) in enumerate(
                        zip(coords[:-1], coords[1:]), counter)]
                counter += len(lines)
                segments.extend(lines)
    return segments
# End segment_multi_polygons function


GEOMETRY_SEGMENT: dict[str, Callable] = {
    ShapeType.linestring: segment_linestrings,
    ShapeType.multi_linestring: segment_multi_linestrings,
    ShapeType.polygon: segment_polygons,
    ShapeType.multi_polygon: segment_multi_polygons,
}


if __name__ == '__main__':  # pragma: no cover
    pass
