#!/usr/bin/env python3
"""Environment checks for Global UG Radar."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


def command_path(name: str) -> str | None:
    return shutil.which(name)


def run_command(args: list[str], timeout: int = 8) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return 127, "", f"{args[0]} not found"
    except subprocess.TimeoutExpired:
        return 124, "", f"{' '.join(args)} timed out"
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def load_countries(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def select_country(countries_config: dict, country_id: str | None) -> dict:
    countries = countries_config.get("countries", {})
    if not country_id:
        return {
            "valid": False,
            "id": None,
            "available": sorted(countries.keys()),
            "note": "Choose one country before provisioning an emulator.",
        }
    profile = countries.get(country_id)
    if not profile:
        return {
            "valid": False,
            "id": country_id,
            "available": sorted(countries.keys()),
            "note": f"Unsupported country: {country_id}",
        }
    return {"valid": True, **profile, "profileVersion": countries_config.get("profileVersion")}


def check_adb_devices() -> dict:
    if not command_path("adb"):
        return {"available": False, "devices": [], "note": "adb not found in PATH"}
    code, stdout, stderr = run_command(["adb", "devices"])
    devices = []
    if code == 0:
        for line in stdout.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 2:
                devices.append({"serial": parts[0], "state": parts[1]})
    return {
        "available": code == 0,
        "devices": devices,
        "note": stderr if code != 0 else "",
    }


def check_emulator_avds() -> dict:
    emulator_path = command_path("emulator")
    if not emulator_path:
        return {"available": False, "path": None, "avds": [], "note": "emulator not found in PATH"}
    code, stdout, stderr = run_command(["emulator", "-list-avds"])
    avds = [line.strip() for line in stdout.splitlines() if line.strip()] if code == 0 else []
    return {
        "available": code == 0,
        "path": emulator_path,
        "avds": avds,
        "note": stderr if code != 0 else "",
    }


def check_state_dir(path: Path) -> dict:
    exists = path.exists()
    expected = ["baseline", "runs", "logs", "secrets"]
    return {
        "path": str(path),
        "exists": exists,
        "expectedSubdirs": expected,
        "missingSubdirs": [name for name in expected if not (path / name).exists()]
        if exists
        else expected,
    }


def check_storage(
    path: Path,
    preferred_gb: int = 24,
    minimum_gb: int = 12,
    reserve_gb: int = 10,
    high_capacity_gb: int = 50,
) -> dict:
    probe = path.expanduser()
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent
    usage = shutil.disk_usage(probe)
    free_gb = usage.free / (1024**3)
    usable_gb = max(0, int(free_gb - reserve_gb))
    target_gb = preferred_gb if usable_gb >= preferred_gb else minimum_gb if usable_gb >= minimum_gb else usable_gb
    ok = target_gb >= minimum_gb
    if target_gb == preferred_gb:
        plan = "default"
    elif ok:
        plan = "minimum"
    else:
        plan = "insufficient"
    return {
        "path": str(probe),
        "preferredGb": preferred_gb,
        "minimumGb": minimum_gb,
        "reserveGb": reserve_gb,
        "highCapacityGb": high_capacity_gb,
        "freeGb": round(free_gb, 1),
        "usableGb": usable_gb,
        "recommendedEmulatorGb": target_gb if ok else None,
        "highCapacityAvailable": usable_gb >= high_capacity_gb,
        "plan": plan,
        "ok": ok,
    }


def check_memory(minimum_gb: int = 8, recommended_gb: int = 16) -> dict:
    total_gb = None
    note = ""
    code, stdout, stderr = run_command(["sysctl", "-n", "hw.memsize"], timeout=5)
    if code == 0 and stdout.strip().isdigit():
        total_gb = int(stdout.strip()) / (1024**3)
    else:
        try:
            pages = os.sysconf("SC_PHYS_PAGES")
            page_size = os.sysconf("SC_PAGE_SIZE")
            total_gb = pages * page_size / (1024**3)
        except (AttributeError, OSError, ValueError):
            note = stderr or "unable to determine physical memory"

    if total_gb is None:
        return {
            "available": False,
            "totalGb": None,
            "minimumGb": minimum_gb,
            "recommendedGb": recommended_gb,
            "plan": "unknown",
            "ok": False,
            "note": note,
        }

    if total_gb >= recommended_gb:
        plan = "recommended"
        ok = True
    elif total_gb >= minimum_gb:
        plan = "low_memory"
        ok = True
    else:
        plan = "insufficient"
        ok = False
    return {
        "available": True,
        "totalGb": round(total_gb, 1),
        "minimumGb": minimum_gb,
        "recommendedGb": recommended_gb,
        "plan": plan,
        "ok": ok,
        "note": note,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Global UG Radar local prerequisites.")
    parser.add_argument("--state-dir", default="~/.global-ug-radar")
    parser.add_argument("--country", choices=["us", "br", "jp", "kr"])
    parser.add_argument("--countries-config", default=str(SKILL_DIR / "config" / "countries.json"))
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only.")
    args = parser.parse_args()

    state_dir = Path(args.state_dir).expanduser()
    countries_config = load_countries(Path(args.countries_config).expanduser())
    country = select_country(countries_config, args.country)

    report = {
        "skill": "global-ug-radar",
        "commands": {
            "python3": command_path("python3"),
            "adb": command_path("adb"),
            "maestro": command_path("maestro"),
            "lark-cli": command_path("lark-cli"),
        },
        "country": country,
        "adb": check_adb_devices(),
        "emulator": check_emulator_avds(),
        "stateDir": check_state_dir(state_dir),
        "storage": check_storage(state_dir),
        "memory": check_memory(),
        "safeToCapture": False,
        "nextSteps": [],
    }

    if not country["valid"]:
        report["nextSteps"].append(country["note"])

    missing = [name for name, path in report["commands"].items() if path is None and name in {"adb", "maestro"}]
    if missing:
        report["nextSteps"].append(
            f"Provision or expose required command(s) in PATH: {', '.join(missing)}"
        )
    if not report["storage"]["ok"]:
        report["nextSteps"].append(
            f"Free more disk space before provisioning the Android research emulator; current free space is {report['storage']['freeGb']}GB at {report['storage']['path']}, minimum emulator size is {report['storage']['minimumGb']}GB plus {report['storage']['reserveGb']}GB reserve."
        )
    elif report["storage"]["plan"] == "minimum":
        report["nextSteps"].append(
            f"Use the minimum Android research emulator size for this machine: {report['storage']['recommendedEmulatorGb']}GB instead of the default {report['storage']['preferredGb']}GB."
        )

    if not report["memory"]["ok"]:
        report["nextSteps"].append(
            f"Do not start a research emulator on this machine yet; physical memory is {report['memory']['totalGb'] or 'unknown'}GB, minimum is {report['memory']['minimumGb']}GB and recommended is {report['memory']['recommendedGb']}GB."
        )
    elif report["memory"]["plan"] == "low_memory":
        report["nextSteps"].append(
            f"Physical memory is {report['memory']['totalGb']}GB. Use the smallest emulator size, avoid parallel heavy apps, and ask before starting the emulator."
        )

    if not report["adb"]["devices"]:
        report["nextSteps"].append(
            "adb devices is 0: this means no device is currently connected to ADB, not that no emulator or app exists."
        )
        if report["emulator"]["available"] and report["emulator"]["avds"]:
            first_avd = country.get("researchAvdName") or country.get("recommendedAvdName") if country.get("valid") else report["emulator"]["avds"][0]
            report["nextSteps"].append(
                f"Start a matching country AVD if present, or run an existing AVD such as: emulator -avd {first_avd}"
            )
        elif report["emulator"]["available"]:
            avd_name = country.get("researchAvdName") or country.get("recommendedAvdName", "global_ug_<country>_google_play")
            report["nextSteps"].append(
                f"Android Emulator is installed but no AVD is listed. Provision Google Play AVD {avd_name} with {report['storage']['recommendedEmulatorGb'] or report['storage']['minimumGb']}GB storage."
            )
        else:
            report["nextSteps"].append(
                "Provision Android Studio / Android Emulator, then run provision_country_avd.py --dry-run and ask for explicit approval before creating or starting the selected-country Google Play AVD."
            )
        report["nextSteps"].append("After the emulator starts, rerun adb devices -l and doctor.py.")

    if report["stateDir"]["missingSubdirs"]:
        report["nextSteps"].append("Initialize local private state directories before a real run.")

    report["safeToCapture"] = (
        country["valid"]
        and not missing
        and report["storage"]["ok"]
        and report["memory"]["ok"]
        and bool(report["adb"]["devices"])
    )

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("Global UG Radar doctor")
        print(f"- state dir: {report['stateDir']['path']}")
        if country["valid"]:
            print(f"- country: {country['id']} ({country['displayName']})")
            print(f"- research AVD: {country.get('researchAvdName') or country['recommendedAvdName']}")
            print(f"- recommended AVD: {country['recommendedAvdName']}")
            print(f"- locale/timezone: {country['locale']} / {country['timezone']}")
        else:
            print(f"- country: invalid ({country.get('note')})")
        for name, path in report["commands"].items():
            print(f"- {name}: {path or 'missing'}")
        devices = report["adb"]["devices"]
        print(f"- adb devices: {len(devices)}")
        for device in devices:
            print(f"  - {device['serial']} ({device['state']})")
        storage = report["storage"]
        print(
            f"- storage free: {storage['freeGb']}GB at {storage['path']} "
            f"(default emulator {storage['preferredGb']}GB, "
            f"recommended {storage['recommendedEmulatorGb'] or 'none'}GB, "
            f"50GB available: {'yes' if storage['highCapacityAvailable'] else 'no'})"
        )
        memory = report["memory"]
        print(
            f"- physical memory: {memory['totalGb'] or 'unknown'}GB "
            f"(minimum {memory['minimumGb']}GB, recommended {memory['recommendedGb']}GB, "
            f"plan {memory['plan']})"
        )
        emulator = report["emulator"]
        print(f"- emulator: {emulator['path'] or 'missing'}")
        if emulator["avds"]:
            print(f"- emulator avds: {', '.join(emulator['avds'])}")
        elif emulator["available"]:
            print("- emulator avds: none")
        print(f"- safe to capture now: {'yes' if report['safeToCapture'] else 'no'}")
        if report["nextSteps"]:
            print("Next steps:")
            for step in report["nextSteps"]:
                print(f"- {step}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
