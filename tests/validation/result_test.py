# -*- coding: utf-8 -*-
"""
Tests for Result Validation
"""

from pytest import mark
from spyops.validation import validate_result


pytestmark = [mark.validation]


def test_validate_result(inputs):
    """
    Test validate result
    """
    fc = inputs['updater_a']
    @validate_result()
    def result_function(result):
        return result
    assert result_function(fc) == fc
# End test_validate_result function


if __name__ == '__main__':  # pragma: no cover
    pass
