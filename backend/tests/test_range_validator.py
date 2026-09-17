from app.services.range_validator import check_ranges

RANGES = {"altitude_m": {"min": 10.0, "max": 120.0}}


def test_in_range_and_boundaries_produce_no_warning():
    assert check_ranges({"altitude_m": 10.0}, RANGES) == []
    assert check_ranges({"altitude_m": 120.0}, RANGES) == []


def test_out_of_range_produces_msg02_warning():
    [w] = check_ranges({"altitude_m": 500.0}, RANGES, leg_position=2)
    assert w["code"] == "MSG02"
    assert (w["field"], w["value"], w["leg_position"]) == ("altitude_m", 500.0, 2)


def test_field_without_known_range_is_ignored():
    assert check_ranges({"payload_kg": 99.0}, RANGES) == []
