from mhxy_hp_overlay.compliance import check_feature_scope


def test_visible_screenshot_allowed():
    decision = check_feature_scope("authorized screenshot visible HP bar analysis")
    assert decision.allowed


def test_memory_forbidden():
    decision = check_feature_scope("read emulator memory to show hidden HP")
    assert not decision.allowed
    assert "memory" in decision.reason


def test_auto_click_forbidden():
    decision = check_feature_scope("visible screen plus auto click battle buttons")
    assert not decision.allowed
