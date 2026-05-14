from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path

from core.diagnostics import (
    ascii_preview,
    extract_ascii_cr_frames,
    hex_dump,
    parse_tx_ascii,
    parse_tx_hex,
    run_manual_transaction,
    run_passive_capture,
    run_single_probe_transaction,
    save_raw_log,
    save_transaction_log,
    select_safe_probe,
)
from core.models import SerialSettings
from core.report import save_json, save_raw, save_txt
from core.scanner import run_active_probe
from protocols import get_profiles
from transport.port_list import list_serial_ports
from transport.serial_transport import SerialPortError, SerialTransport


BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "reports"
LOGS_DIR = BASE_DIR / "logs"


def profiles_map(include_unverified: bool = False):
    return {p.id: p for p in get_profiles(include_unverified=include_unverified)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list-ports", action="store_true")
    parser.add_argument("--list-profiles", action="store_true")
    parser.add_argument("--scan", action="store_true")
    parser.add_argument("--passive", action="store_true")
    parser.add_argument("--doctor", action="store_true")
    parser.add_argument("--single-probe", action="store_true")
    parser.add_argument("--print-jk-pylon-checklist", action="store_true")
    manual = parser.add_mutually_exclusive_group()
    manual.add_argument("--tx-ascii")
    manual.add_argument("--tx-hex")
    parser.add_argument("--port")
    parser.add_argument("--baud", type=int, default=9600)
    parser.add_argument("--bytesize", type=int, default=8)
    parser.add_argument("--parity", default="N")
    parser.add_argument("--stopbits", type=int, default=1)
    parser.add_argument("--seconds", type=int, default=10)
    parser.add_argument("--timeout-ms", type=int, default=1500)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--delay-ms", type=int, default=0)
    parser.add_argument("--profile")
    parser.add_argument("--probe")
    parser.add_argument("--profiles")
    parser.add_argument("--include-unverified", action="store_true")
    return parser


def _settings_from_args(args: argparse.Namespace) -> SerialSettings:
    return SerialSettings(
        baudrate=args.baud,
        parity=args.parity,
        bytesize=args.bytesize,
        stopbits=args.stopbits,
        timeout=args.timeout_ms / 1000,
    )


def _require_port(args: argparse.Namespace, mode: str) -> None:
    if not args.port:
        raise ValueError(f"--port is required for {mode}")


def _print_transaction_entry(entry) -> None:
    print(f"Attempt: {entry.attempt}")
    print(f"TX ASCII: {entry.tx_ascii}")
    print(f"TX HEX: {entry.tx_hex}")
    print(f"RX LEN: {entry.rx_len}")
    print(f"RX ASCII preview: {entry.rx_ascii_preview}")
    print(f"RX HEX: {entry.rx_hex}")
    print(f"Frames found: {entry.frames_found}")
    print("Validation reasons:")
    for reason in entry.validation_reasons:
        print(f"- {reason}")
    if entry.decoded and entry.decoded.get("decode_status"):
        print("Decoded:")
        for key, value in entry.decoded.items():
            if key == "raw_hex":
                continue
            print(f"- {key}: {value}")
    if entry.hardware_status:
        print("Hardware status:")
        for item in entry.hardware_status:
            print(f"- {item}")


def _print_passive(data: bytes, raw_log_path: Path) -> None:
    frames = extract_ascii_cr_frames(data)
    print(f"Captured bytes: {len(data)}")
    if data:
        print(f"HEX dump: {hex_dump(data)}")
        print(f"ASCII preview: {ascii_preview(data)}")
        print(f"Detected ~...\\r frames: {len(frames)}")
        for idx, frame in enumerate(frames, start=1):
            print(f"- frame {idx}: {ascii_preview(frame)}")
    else:
        print("No data received during passive listen window.")
        print("This means only that this adapter received no bytes. It does not prove the BMS is dead.")
        print("Detected ~...\\r frames: 0")
    print(f"Raw log path: {raw_log_path}")


def _print_jk_pylon_checklist() -> None:
    lines = [
        "JK app: UART Protocol = 014 PYLON_low_voltage_Protocol",
        "Device Addr = 1",
        "USB-RS485 A -> JK yellow",
        "USB-RS485 B -> JK white",
        "GND not used in short bench test",
        "Serial 9600 8N1",
        "close official JK-BMS-MONITOR before opening COM",
        "first probe: ~201246620000FDA9\\r",
        "expected RX prefix: ~200246",
    ]
    print("\n".join(lines))


def _run_doctor(
    args: argparse.Namespace,
    transport_factory: Callable[[], SerialTransport],
    list_ports_func: Callable[[], list[str]],
) -> int:
    _require_port(args, "--doctor")
    ports = list_ports_func()
    print("Available ports:")
    if ports:
        for item in ports:
            print(f"- {item}")
    else:
        print("- <none>")
    if args.port not in ports:
        print(f"Selected port exists: no ({args.port})")
        return 2
    print(f"Selected port exists: yes ({args.port})")

    transport = transport_factory()
    transport.open(args.port, _settings_from_args(args))
    try:
        actual_settings = getattr(transport, "actual_settings")()
        print("Open: OK")
        print("Actual settings:")
        for key in ("port", "baudrate", "bytesize", "parity", "stopbits", "timeout"):
            print(f"- {key}: {actual_settings.get(key)}")
    finally:
        transport.close()
    print("Close: OK")
    print("This only proves OS-level port access, not RS485 wiring or BMS response.")
    return 0


def run_cli(
    args: argparse.Namespace,
    transport_factory: Callable[[], SerialTransport] = SerialTransport,
    list_ports_func: Callable[[], list[str]] = list_serial_ports,
    log_dir: Path | None = None,
) -> int:
    if log_dir is None:
        log_dir = LOGS_DIR
    pmap = profiles_map(include_unverified=args.include_unverified)
    if args.list_ports:
        print("\n".join(list_ports_func()))
        return 0
    if args.list_profiles:
        for p in pmap.values():
            risks = sorted({probe.risk for probe in p.probes})
            print(f"{p.id}\t{p.name}\tenabled={p.enabled_by_default}\trisks={','.join(risks)}")
        return 0
    if args.print_jk_pylon_checklist:
        _print_jk_pylon_checklist()
        return 0
    if args.doctor:
        return _run_doctor(args, transport_factory, list_ports_func)

    if args.tx_ascii is not None or args.tx_hex is not None:
        _require_port(args, "manual TX mode")
        print("Manual TX mode bypasses profile selection. Use only verified read-only frames.")
        tx = parse_tx_ascii(args.tx_ascii) if args.tx_ascii is not None else parse_tx_hex(args.tx_hex)
        entry = run_manual_transaction(
            transport=transport_factory(),
            port=args.port,
            settings=_settings_from_args(args),
            tx=tx,
            timeout_ms=args.timeout_ms,
        )
        _print_transaction_entry(entry)
        log_path = save_transaction_log([entry], log_dir, prefix="manual_tx")
        print(f"Transaction log: {log_path}")
        return 0

    if args.single_probe:
        _require_port(args, "--single-probe")
        if not args.profile:
            raise ValueError("--profile is required for --single-probe")
        if not args.probe:
            raise ValueError("--probe is required for --single-probe")
        if args.profile not in pmap:
            raise ValueError(f"Invalid profile id: {args.profile}")
        profile = pmap[args.profile]
        probe = select_safe_probe(profile, args.probe, include_unverified=args.include_unverified)
        if probe.risk == "experimental_unverified_read":
            if "cell_voltage" in probe.name or "cell_voltages" in probe.name:
                request_kind = "cell-voltage block request"
            else:
                request_kind = "block request" if (probe.quantity or 0) > 1 else "request"
            print("WARNING:")
            print(f"This is an experimental unverified read-only FC03 {request_kind}.")
            print("It is not source-confirmed.")
            print(f"BMS menu must be set to {getattr(profile, 'bms_menu', profile.id)}.")
            print("No scan will be run.")
        entries = run_single_probe_transaction(
            transport=transport_factory(),
            port=args.port,
            settings=_settings_from_args(args),
            profile=profile,
            probe=probe,
            timeout_ms=args.timeout_ms,
            repeat=args.repeat,
            delay_ms=args.delay_ms,
        )
        print(f"Profile: {profile.id}")
        print(f"Probe: {probe.name}")
        for entry in entries:
            _print_transaction_entry(entry)
        log_path = save_transaction_log(entries, log_dir, prefix=f"single_probe_{profile.id}_{probe.name}")
        print(f"Transaction log: {log_path}")
        return 0

    if args.passive:
        _require_port(args, "--passive")
        data = run_passive_capture(
            transport=transport_factory(),
            port=args.port,
            settings=_settings_from_args(args),
            seconds=args.seconds,
        )
        raw_log_path = save_raw_log(data, log_dir, prefix="passive")
        _print_passive(data, raw_log_path)
        return 0

    if args.scan:
        _require_port(args, "--scan")
        try:
            selected = pmap.values() if not args.profiles else [pmap[p.strip()] for p in args.profiles.split(",")]
        except KeyError as exc:
            raise ValueError(f"Invalid profile id: {exc.args[0]}") from exc
        found = False
        for profile in selected:
            result = run_active_probe(transport_factory(), args.port, profile, include_unverified=args.include_unverified)
            print(f"{profile.id}: score={result.score} raw_score={result.raw_score} status={result.status}")
            out = REPORTS_DIR
            out.mkdir(parents=True, exist_ok=True)
            save_json(result, out / f"{profile.id}.json")
            save_txt(result, out / f"{profile.id}.txt")
            save_raw(result, LOGS_DIR / f"{profile.id}.raw.log")
            found = found or result.detected
        if not found:
            print("No protocol detected under tested profiles. Check physical interface, wake state, pinout, baudrate, address, and BMS app settings.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return run_cli(args)
    except SerialPortError:
        print("COM port busy or access denied. Close other serial tools and retry.")
        return 2
    except RuntimeError as exc:
        print(f"Internal error: {exc}")
        return 1
    except ValueError as exc:
        print(f"Error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
