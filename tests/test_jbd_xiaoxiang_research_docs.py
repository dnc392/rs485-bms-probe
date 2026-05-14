from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
RESEARCH_DIR = PROJECT_DIR / "docs" / "protocol_research"


def test_jbd_xiaoxiang_probe_frames_yaml_documents_active_safe_read_policy():
    text = (RESEARCH_DIR / "jbd_xiaoxiang_probe_frames.yaml").read_text(encoding="utf-8")

    assert "protocol: jbd_xiaoxiang_uart_rs485" in text
    assert "status: active_safe_read" in text
    assert 'tx_hex: "DD A5 03 00 FF FD 77"' in text
    assert 'tx_hex: "DD A5 04 00 FF FC 77"' in text
    assert "source_status: confirmed_by_public_sources" in text
    assert "mos_control" in text
    assert "capacity_reset" in text
    assert "No write/control frames are active." in text


def test_jbd_xiaoxiang_markdown_records_sources_and_raw_only_policy():
    text = (RESEARCH_DIR / "jbd_xiaoxiang_uart_rs485.md").read_text(encoding="utf-8")

    assert "Primary open references" in text
    assert "First hardware test sequence" in text
    assert "JBD communication protocol new-RS485,RS232,UART" in text
    assert "DD A5 03 00 FF FD 77" in text
    assert "DD A5 04 00 FF FC 77" in text
    assert "--probe read_basic_info" in text
    assert "--probe read_cell_voltages" in text
    assert "status == 0x00" in text
    assert "Field-level decoding is deferred" in text


def test_sources_index_records_jbd_source_family():
    text = (RESEARCH_DIR / "sources.md").read_text(encoding="utf-8")

    assert "JBD / Xiaoxiang UART-RS485" in text
    assert "DD CMD STATUS LEN DATA" in text
    assert "syssi/esphome-jbd-bms" in text
