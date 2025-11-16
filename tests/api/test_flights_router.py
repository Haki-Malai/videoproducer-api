import pytest

from api.v1.flights import _parse_bbox


def test_parse_bbox_returns_float_tuple():
    assert _parse_bbox("10.5,20.1,30.2,40.3") == (10.5, 20.1, 30.2, 40.3)


@pytest.mark.parametrize("raw", ["1,2,3", "1,2,3,4,5"])
def test_parse_bbox_rejects_invalid_payload_counts(raw: str):
    with pytest.raises(ValueError):
        _parse_bbox(raw)


def test_parse_bbox_requires_numeric_values():
    with pytest.raises(ValueError):
        _parse_bbox("west,2,3,4")
