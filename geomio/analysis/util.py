# -*- coding: utf-8 -*-
"""
Utility functions in support of analysis
"""


from fudgeo import FeatureClass

from geomio.shared.query import QueryAnalysis
from geomio.shared.base import AnalysisComponents
from geomio.shared.constant import SQL_EMPTY
from geomio.shared.element import copy_feature_class


def build_analysis(source: FeatureClass, target: FeatureClass,
                   operator: FeatureClass) -> AnalysisComponents:
    """
    Build the components needed for an Analysis
    """
    query = QueryAnalysis(source, target=target, operator=operator)
    target = copy_feature_class(source, target=target, where_clause=SQL_EMPTY)
    return AnalysisComponents(
        has_intersection=query.has_intersection, query=query, target=target)
# End build_analysis function


if __name__ == '__main__':  # pragma: no cover
    pass
