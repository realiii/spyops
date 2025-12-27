# -*- coding: utf-8 -*-
"""
Query Classes for analysis.overlay module
"""

from geomio.query.base import AbstractSpatialAttribute
from geomio.query.extract import QueryClip


class QueryErase(QueryClip):
    """
    Queries for Erase
    """
# End QueryErase class


class QueryIntersectPairwise(AbstractSpatialAttribute):
    """
    Queries for Intersect (Pairwise)
    """
# End QueryIntersectPairwise class


if __name__ == '__main__':  # pragma: no cover
    pass
