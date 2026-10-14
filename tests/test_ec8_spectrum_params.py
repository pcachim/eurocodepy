"""``get_spectrum_parameters`` (self-contained tables) agrees with ``get_spec_params`` (database)."""
import pytest

from eurocodepy.ec8 import get_spec_params, get_spectrum_parameters


@pytest.mark.parametrize("zone", ["1_1", "1_2", "1_3", "1_4", "1_5", "1_6"])
@pytest.mark.parametrize("soil", ["A", "C", "E"])
def test_pt1_matches_the_database(zone, soil):
    assert get_spectrum_parameters("PT-1", "ii", soil, zone) == pytest.approx(
        get_spec_params("PT", "PT1", "II", soil, zone))


def test_cen1_matches_the_database():
    assert get_spectrum_parameters("CEN-1", "ii", "C", ".2g") == pytest.approx(
        get_spec_params("EU", "CEN_1", "II", "C", ".2g"))
