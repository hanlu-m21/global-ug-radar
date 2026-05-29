#!/usr/bin/env python3
"""Provision a country-specific Android Google Play research AVD."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SYSTEM_IMAGE_API = "35"
DEFAULT_DEVICE = "pixel_7"


def command_path(name: str) -> str | None:
    return shutil.which(name)


def run_command(
    args: list[str],
    timeout: int = 30,
    input_text: str | None = None,
) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            args,
            input=input_text,
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


def avd_home() -> Path:
    return Path(os.environ.get("ANDROID_AVD_HOME", str(Path.home() / ".android" / "avd"))).expanduser()


def avd_dir(avd_name: str) -> Path:
    return avd_home() / f"{avd_name}.avd"


def list_avds() -> list[str]:
    if not command_path("emulator"):
        return []
    code, stdout, _ = run_command(["emulator", "-list-avds"], timeout=15)
    if code != 0:
        return []
    return [line.strip() for line in stdout.splitlines() if line.strip()]


def system_image_package(api: str) -> str:
    abi = "arm64-v8a" if platform.machine().lower() in {"arm64", "aarch64"} else "x86_64"
    return f"system-images;android-{api};google_apis_playstore;{abi}"


def create_avd(avd_name: str, package: str, device: str, dry_run: bool) -> dict:
    cmd = ["avdmanager", "create", "avd", "-n", avd_name, "-k", package, "-d", device]
    if dry_run:
        return {"planned": True, "command": cmd}
    code, stdout, stderr = run_command(cmd, timeout=120, input_text="no\n")
    return {"planned": False, "command": cmd, "returnCode": code, "stdout": stdout, "stderr": stderr}


def update_config_ini(path: Path, storage_gb: int, dry_run: bool) -> dict:
    desired = {
        "PlayStore.enabled": "yes",
        "disk.dataPartition.size": f"{storage_gb}G",
        "fastboot.forceColdBoot": "yes",
        "fastboot.forceFastBoot": "no",
        "firstboot.bootFromDownloadableSnapshot": "no",
        "firstboot.bootFromLocalSnapshot": "no",
        "firstboot.saveToLocalSnapshot": "no",
    }
    if dry_run:
        return {"path": str(path), "planned": desired}
    if not path.exists():
        return {"path": str(path), "error": "config.ini not found"}
    lines = path.read_text(encoding="utf-8").splitlines()
    seen = set()
    updated = []
    for line in lines:
        if "=" not in line:
            updated.append(line)
            continue
        key, _ = line.split("=", 1)
        if key in desired:
            updated.append(f"{key}={desired[key]}")
            seen.add(key)
        else:
            updated.append(line)
    for key, value in desired.items():
        if key not in seen:
            updated.append(f"{key}={value}")
    path.write_text("\n".join(updated) + "\n", encoding="utf-8")
    return {"path": str(path), "applied": desired}


def find_icc_template(state_dir: Path, selected_avd_dir: Path) -> Path | None:
    candidates = [
        state_dir / "profiles" / "_template" / "iccprofile_for_sim0.xml",
        SKILL_DIR / "assets" / "iccprofile_android_emulator_base.xml",
        selected_avd_dir / "modem_simulator" / "iccprofile_for_sim0.xml",
    ]
    candidates.extend(sorted(avd_home().glob("*/modem_simulator/iccprofile_for_sim0.xml")))
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def write_country_icc(template: Path, output: Path, sim_profile: dict, dry_run: bool) -> dict:
    if not sim_profile:
        return {"path": None, "note": "country profile has no simProfile"}
    if dry_run:
        return {
            "path": str(output),
            "template": str(template),
            "planned": {
                "imsi": sim_profile["imsi"],
                "mncLength": sim_profile["mncLength"],
                "operatorNumeric": sim_profile["operatorNumeric"],
            },
        }
    content = template.read_text(encoding="utf-8")
    content, imsi_count = re.subn(r"<CIMI>[^<]+</CIMI>", f"<CIMI>{sim_profile['imsi']}</CIMI>", content, count=1)
    content, ad_count = re.subn(
        r"144,0,0000000[0-9A-Fa-f](?=</SIMIO>)",
        f"144,0,0000000{int(sim_profile['mncLength'])}",
        content,
        count=1,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    return {
        "path": str(output),
        "template": str(template),
        "updated": {"imsi": imsi_count, "mncLength": ad_count},
        "simProfile": sim_profile,
    }


def wait_for_boot(timeout_seconds: int) -> dict:
    run_command(["adb", "wait-for-device"], timeout=timeout_seconds)
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        code, stdout, stderr = run_command(["adb", "shell", "getprop sys.boot_completed"], timeout=8)
        if code == 0 and stdout.strip() == "1":
            return {"booted": True}
        time.sleep(3)
    return {"booted": False, "error": "boot timeout"}


def check_memory(minimum_gb: int = 8, recommended_gb: int = 16) -> dict:
    code, stdout, stderr = run_command(["sysctl", "-n", "hw.memsize"], timeout=5)
    total_gb = None
    note = ""
    if code == 0 and stdout.strip().isdigit():
        total_gb = int(stdout.strip()) / (1024**3)
    else:
        note = stderr or "unable to determine physical memory"
    if total_gb is None:
        return {
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
        "totalGb": round(total_gb, 1),
        "minimumGb": minimum_gb,
        "recommendedGb": recommended_gb,
        "plan": plan,
        "ok": ok,
        "note": note,
    }


def start_emulator(avd_name: str, icc_profile: Path | None, dry_run: bool) -> dict:
    cmd = [
        "emulator",
        "-avd",
        avd_name,
        "-no-snapshot-load",
        "-no-snapshot-save",
    ]
    if icc_profile:
        cmd.extend(["-icc-profile", str(icc_profile)])
    if dry_run:
        return {"planned": True, "command": cmd}
    process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    return {"planned": False, "command": cmd, "pid": process.pid}


def apply_runtime_profile(profile: dict, dry_run: bool) -> dict:
    commands = [
        ["adb", "shell", "cmd", "alarm", "set-timezone", profile["timezone"]],
        ["adb", "emu", "geo", "fix", str(profile["geo"]["longitude"]), str(profile["geo"]["latitude"])],
        ["adb", "shell", "settings", "put", "system", "system_locales", profile["locale"]],
        ["adb", "shell", "am", "start", "-a", "android.settings.LOCALE_SETTINGS"],
    ]
    if dry_run:
        return {"plannedCommands": commands}
    results = []
    for command in commands:
        code, stdout, stderr = run_command(command, timeout=15)
        results.append({"command": command, "returnCode": code, "stdout": stdout, "stderr": stderr})
    return {"commands": results}


def main() -> int:
    parser = argparse.ArgumentParser(description="Provision a country-specific Google Play research AVD.")
    parser.add_argument("--state-dir", default="~/.global-ug-radar")
    parser.add_argument("--country", required=True, choices=["us", "br", "jp", "kr"])
    parser.add_argument("--countries-config", default=str(SKILL_DIR / "config" / "countries.json"))
    parser.add_argument("--avd-name")
    parser.add_argument("--storage-gb", type=int, default=24)
    parser.add_argument("--system-image-api", default=DEFAULT_SYSTEM_IMAGE_API)
    parser.add_argument("--device", default=DEFAULT_DEVICE)
    parser.add_argument("--start", action="store_true", help="Start the AVD after provisioning and open Android language settings.")
    parser.add_argument("--confirm-resource-use", action="store_true", help="Required for real AVD creation, config writes, or emulator start.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()

    state_dir = Path(args.state_dir).expanduser()
    countries_config = load_countries(Path(args.countries_config).expanduser())
    profile = countries_config["countries"][args.country]
    avd_name = args.avd_name or profile.get("researchAvdName") or profile["recommendedAvdName"]
    selected_avd_dir = avd_dir(avd_name)
    package = system_image_package(args.system_image_api)

    missing_commands = [name for name in ["avdmanager", "emulator", "adb"] if not command_path(name)]
    existing_avds = list_avds()
    memory_result = check_memory()
    resource_blockers = []
    if not args.dry_run and not args.confirm_resource_use:
        resource_blockers.append("resource_confirmation_required")
    if not args.dry_run and not memory_result["ok"]:
        resource_blockers.append("memory_insufficient")
    if args.storage_gb < 12:
        resource_blockers.append("storage_too_small")
    resource_blocked = bool(resource_blockers)

    created = None
    if avd_name not in existing_avds:
        if resource_blocked and not args.dry_run:
            created = {"skipped": True, "reason": ",".join(resource_blockers)}
        else:
            created = create_avd(avd_name, package, args.device, args.dry_run)

    if resource_blocked and not args.dry_run:
        config_result = {"path": str(selected_avd_dir / "config.ini"), "skipped": True, "reason": ",".join(resource_blockers)}
    else:
        config_result = update_config_ini(selected_avd_dir / "config.ini", args.storage_gb, args.dry_run)

    icc_template = find_icc_template(state_dir, selected_avd_dir)
    icc_profile_path = state_dir / "profiles" / args.country / f"iccprofile_{args.country}.xml"
    icc_result = None
    if icc_template:
        if resource_blocked and not args.dry_run:
            icc_result = {"path": str(icc_profile_path), "skipped": True, "reason": ",".join(resource_blockers)}
        else:
            icc_result = write_country_icc(icc_template, icc_profile_path, profile.get("simProfile", {}), args.dry_run)

    start_result = None
    boot_result = None
    runtime_result = None
    if args.start and not missing_commands and not resource_blocked:
        start_result = start_emulator(avd_name, icc_profile_path if icc_template else None, args.dry_run)
        if not args.dry_run:
            boot_result = wait_for_boot(180)
            if boot_result.get("booted"):
                runtime_result = apply_runtime_profile(profile, args.dry_run)

    blockers = list(resource_blockers)
    if missing_commands:
        blockers.append("android_tools_missing")
    if created and created.get("returnCode") not in {None, 0}:
        blockers.append("avd_create_failed")
    if not args.dry_run and config_result.get("error"):
        blockers.append("avd_config_missing")
    if not icc_template and profile.get("simProfile"):
        blockers.append("icc_template_missing")

    result = {
        "status": "ready" if not blockers else "blocked",
        "checkedAt": datetime.now(timezone.utc).astimezone().isoformat(),
        "country": {
            "id": profile["id"],
            "displayName": profile["displayName"],
            "profileVersion": countries_config.get("profileVersion"),
            "locale": profile["locale"],
            "timezone": profile["timezone"],
            "networkCountry": profile["networkCountry"],
            "geo": profile["geo"],
            "simProfile": profile.get("simProfile"),
            "playStoreUiSignals": profile.get("playStoreUiSignals", []),
        },
        "avd": {
            "name": avd_name,
            "dir": str(selected_avd_dir),
            "systemImage": package,
            "device": args.device,
            "storageGb": args.storage_gb,
            "existedBefore": avd_name in existing_avds,
            "create": created,
            "config": config_result,
        },
        "resourcePlan": {
            "storageGb": args.storage_gb,
            "storageMode": "high_capacity" if args.storage_gb >= 50 else "default",
            "memory": memory_result,
            "requiresConfirmation": not args.dry_run,
            "confirmed": args.confirm_resource_use,
        },
        "iccProfile": icc_result or {"path": str(icc_profile_path), "template": None},
        "start": start_result,
        "boot": boot_result,
        "runtime": runtime_result,
        "blockers": blockers,
        "nextSteps": [],
    }

    if "android_tools_missing" in blockers:
        result["nextSteps"].append(f"Expose required Android commands in PATH: {', '.join(missing_commands)}.")
    if "resource_confirmation_required" in blockers:
        result["nextSteps"].append("Review this plan with the user, then rerun with --confirm-resource-use only after explicit approval.")
    if "memory_insufficient" in blockers:
        result["nextSteps"].append("Do not start the emulator on this machine; use an existing device/emulator or a higher-memory host.")
    if "storage_too_small" in blockers:
        result["nextSteps"].append("Use at least 12GB storage for the research emulator.")
    if "avd_create_failed" in blockers:
        result["nextSteps"].append(f"Install the Google Play system image first: sdkmanager '{package}', then rerun this script.")
    if "icc_template_missing" in blockers:
        result["nextSteps"].append("Start any Android emulator once so modem_simulator/iccprofile_for_sim0.xml exists, or place a base profile at ~/.global-ug-radar/profiles/_template/iccprofile_for_sim0.xml.")
    if args.storage_gb >= 50:
        result["nextSteps"].append("50GB is high-capacity mode; use it only when the user explicitly requested it.")
    if args.start and not resource_blocked and not missing_commands:
        result["nextSteps"].append("In Android Language settings, add/select the profile language and move it to the first position; verify with: adb shell am get-config.")
    elif args.start:
        result["nextSteps"].append("The emulator was not started because provisioning is blocked; resolve blockers before using --start.")
    elif not blockers:
        launch = ["emulator", "-avd", avd_name, "-no-snapshot-load", "-no-snapshot-save"]
        if icc_template:
            launch.extend(["-icc-profile", str(icc_profile_path)])
        result["nextSteps"].append("Start the emulator with: " + " ".join(launch))
        result["nextSteps"].append("After boot, apply timezone/geolocation and open Android Language settings; then run verify_country_env.py.")
    else:
        result["nextSteps"].append("Do not start the emulator until blockers are resolved and resource use is confirmed.")

    output = Path(args.output).expanduser() if args.output else state_dir / "logs" / f"provision-avd-{args.country}.json"
    if not args.dry_run:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
