from __future__ import annotations

import argparse
from pathlib import Path

from core.models import SerialSettings
from core.report import save_json, save_raw, save_txt
from core.scanner import run_active_probe, run_passive_listen
from protocols import get_all_profiles
from transport.port_list import list_serial_ports
from transport.serial_transport import SerialTransport


def profiles_map():
    return {p.id: p for p in get_all_profiles()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list-ports", action="store_true")
    parser.add_argument("--list-profiles", action="store_true")
    parser.add_argument("--scan", action="store_true")
    parser.add_argument("--passive", action="store_true")
    parser.add_argument("--port")
    parser.add_argument("--baud", type=int, default=9600)
    parser.add_argument("--seconds", type=int, default=10)
    parser.add_argument("--profiles")
    parser.add_argument("--include-unverified", action="store_true")
    args = parser.parse_args()

    pmap = profiles_map()
    if args.list_ports:
        print("\n".join(list_serial_ports()))
        return
    if args.list_profiles:
        for p in pmap.values():
            risks = sorted({probe.risk for probe in p.probes})
            print(f"{p.id}\t{p.name}\tenabled={p.enabled_by_default}\trisks={','.join(risks)}")
        return

    if args.passive:
        if not args.port:
            raise SystemExit("--port is required for --passive")
        try:
            data = run_passive_listen(SerialTransport(), args.port, SerialSettings(baudrate=args.baud), seconds=args.seconds)
        except Exception:
            raise SystemExit("COM port busy or access denied. Close other serial tools and retry.")
        if data["bytes"] == 0:
            print("No data received during passive listen window.")
        else:
            print(f"Captured bytes: {data['bytes']}")
        return

    if args.scan:
        if not args.port:
            raise SystemExit("--port is required for --scan")
        try:
            selected = pmap.values() if not args.profiles else [pmap[p.strip()] for p in args.profiles.split(",")]
        except KeyError as exc:
            raise SystemExit(f"Invalid profile id: {exc.args[0]}")
        found = False
        for profile in selected:
            try:
                result = run_active_probe(SerialTransport(), args.port, profile, include_unverified=args.include_unverified)
            except Exception:
                raise SystemExit("COM port busy or access denied. Close other serial tools and retry.")
            print(f"{profile.id}: score={result.score} status={result.status}")
            out = Path("bms_probe/reports")
            out.mkdir(parents=True, exist_ok=True)
            save_json(result, out / f"{profile.id}.json")
            save_txt(result, out / f"{profile.id}.txt")
            save_raw(result, Path("bms_probe/logs") / f"{profile.id}.raw.log")
            found = found or result.detected
        if not found:
            print("No protocol detected under tested profiles. Check physical interface, wake state, pinout, baudrate, address, and BMS app settings.")


if __name__ == "__main__":
    main()
