from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
MATRIX = PROJECT_DIR / "docs" / "protocol_research" / "jk_protocol_modes_matrix.md"


def test_jk_protocol_modes_matrix_exists():
    assert MATRIX.is_file()


def test_jk_protocol_modes_matrix_contains_required_terms():
    text = MATRIX.read_text(encoding="utf-8")

    assert "Do not test non-Pylon modes with Pylon requests" in text
    assert "If no confirmed request exists, mark TX as `TBD` and do not test." in text
    assert "Growatt" in text
    assert "TBD" in text
    assert "Pylon LV" in text
