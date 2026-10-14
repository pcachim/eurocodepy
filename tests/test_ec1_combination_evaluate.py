"""``LoadCombination.evaluate`` (used by ``LoadCombinations.evaluate_all`` and ``worst_case``)."""
import numpy as np
import pytest

from eurocodepy.ec1 import Load, LoadCombinations, LoadType, Loads


def _loads():
    loads = Loads()
    loads.add(Load("G", LoadType.PERMANENT, 1.0, 1.35, 0.0, 0.0, 0.0))
    loads.add(Load("Q", LoadType.LIVE, 0.0, 1.5, 0.7, 0.5, 0.3))
    return loads


def test_evaluate_sums_the_factored_values():
    combo = next(iter(_loads().get_ULS_combos().values()))
    assert combo.evaluate({"G": 10.0, "Q": 5.0}) == pytest.approx(1.35 * 10.0 + 1.5 * 5.0)


def test_worst_case_over_arrays():
    combos = LoadCombinations(_loads().get_ULS_combos().values())
    name, env = combos.worst_case({"G": np.array([10.0, 20.0]), "Q": np.array([5.0, 0.0])})
    assert env == pytest.approx([1.35 * 10.0 + 7.5, 1.35 * 20.0])
