from core.scorer import detected_from_score


def test_detected_threshold():
    assert detected_from_score(80)
    assert not detected_from_score(79)
