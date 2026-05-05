import pytest

from mhxy_hp_overlay.roi import crop_box_size, parse_roi


def test_parse_roi():
    assert parse_roi("1,2,11,22") == (1, 2, 11, 22)
    assert crop_box_size((1, 2, 11, 22)) == (10, 20)


def test_parse_roi_rejects_bad_shape():
    with pytest.raises(ValueError):
        parse_roi("1,2,3")


def test_parse_roi_rejects_inverted():
    with pytest.raises(ValueError):
        parse_roi("10,10,5,20")
