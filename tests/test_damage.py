from PIL import Image

from mhxy_hp_overlay.damage import (
    DamageTracker,
    analyze_damage_roi,
    extract_damage_numbers,
    summarize_damage_numbers,
)


def test_extract_damage_numbers_includes_healing_and_ignores_ratios_by_default():
    text = "暴击 2388\n+1042\n气血 1234/5678\n-666\n891"

    assert extract_damage_numbers(text) == [2388, 1042, 666, 891]


def test_extract_damage_numbers_can_exclude_healing():
    text = "暴击 2388\n+1042\n气血 1234/5678\n-666\n891"

    assert extract_damage_numbers(text, include_healing=False) == [2388, 666, 891]


def test_extract_damage_numbers_respects_min_amount():
    assert extract_damage_numbers("21 970 1000", min_amount=100) == [970, 1000]


def test_summarize_damage_numbers():
    summary = summarize_damage_numbers([2388, 666, 891], name="round1")

    assert summary.name == "round1"
    assert summary.count == 3
    assert summary.total_damage == 3945
    assert summary.max_damage == 2388
    assert summary.average_damage == 1315.0


def test_analyze_damage_roi_with_visible_text():
    image = Image.new("RGB", (100, 50), "black")

    summary = analyze_damage_roi(image, (0, 0, 100, 50), name="attack1", visible_text="暴击 2024 +500")

    assert summary.name == "attack1"
    assert summary.numbers == [2024, 500]
    assert summary.total_damage == 2524


def test_analyze_damage_roi_can_exclude_healing():
    image = Image.new("RGB", (100, 50), "black")

    summary = analyze_damage_roi(
        image,
        (0, 0, 100, 50),
        name="attack1",
        visible_text="暴击 2024 +500",
        include_healing=False,
    )

    assert summary.numbers == [2024]
    assert summary.total_damage == 2024


def test_damage_tracker_deduplicates_recent_same_number():
    tracker = DamageTracker(dedupe_window_seconds=1.0)

    first = tracker.add_numbers([1000, 888], timestamp=10.0, source="frame1")
    second = tracker.add_numbers([1000, 777], timestamp=10.5, source="frame2")
    third = tracker.add_numbers([1000], timestamp=11.5, source="frame3")

    assert [event.amount for event in first] == [1000, 888]
    assert [event.amount for event in second] == [777]
    assert [event.amount for event in third] == [1000]
    assert tracker.summary().total_damage == 3665
    assert tracker.summary().count == 4
