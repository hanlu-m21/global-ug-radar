#!/usr/bin/env python3
"""Verify the selected country environment before Global UG Radar research."""

from __future__ import annotations

import argparse
import json
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


def load_countries(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


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


def adb_shell(command: str, timeout: int = 8) -> tuple[int, str, str]:
    return run_command(["adb", "shell", command], timeout=timeout)


def adb_devices() -> list[dict]:
    code, stdout, _ = run_command(["adb", "devices"])
    if code != 0:
        return []
    devices = []
    for line in stdout.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2:
            devices.append({"serial": parts[0], "state": parts[1]})
    return devices


def fetch_json(url: str, timeout: int) -> tuple[dict | None, str | None]:
    request = urllib.request.Request(url, headers={"User-Agent": "global-ug-radar/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8")), None
    except urllib.error.HTTPError as exc:
        return None, f"http_{exc.code}"
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return None, str(exc)


def normalize_network_payload(provider: str, payload: dict) -> dict:
    if provider == "ipinfo":
        return {
            "provider": provider,
            "country": payload.get("country"),
            "region": payload.get("region"),
            "city": payload.get("city"),
            "ip": payload.get("ip"),
        }
    if provider == "ipwhois":
        return {
            "provider": provider,
            "country": payload.get("country_code") if payload.get("success", True) else None,
            "region": payload.get("region"),
            "city": payload.get("city"),
            "ip": payload.get("ip"),
        }
    if provider == "ipapi":
        return {
            "provider": provider,
            "country": payload.get("countryCode") if payload.get("status") == "success" else None,
            "region": payload.get("regionName"),
            "city": payload.get("city"),
            "ip": payload.get("query"),
        }
    raise ValueError(f"Unknown provider: {provider}")


def host_network_country(timeout: int = 6) -> dict:
    providers = [
        ("ipinfo", "https://ipinfo.io/json"),
        ("ipwhois", "https://ipwho.is/"),
        ("ipapi", "http://ip-api.com/json/?fields=status,country,countryCode,regionName,city,query,message"),
    ]
    attempts = []
    for provider, url in providers:
        payload, error = fetch_json(url, timeout)
        if error:
            attempts.append({"provider": provider, "available": False, "error": error})
            continue
        normalized = normalize_network_payload(provider, payload or {})
        attempts.append({"available": True, **normalized})
        if normalized.get("country"):
            return {"available": True, **normalized, "attempts": attempts}
    return {"available": False, "country": None, "attempts": attempts, "error": "no_network_country_provider_available"}


def getprop(name: str) -> str:
    _, stdout, _ = adb_shell(f"getprop {name}")
    return stdout.strip()


def locale_to_config_token(locale: str) -> str:
    normalized = locale.replace("_", "-")
    if "-" not in normalized:
        return normalized
    language, region = normalized.split("-", 1)
    return f"{language}-r{region.upper()}"


def mnc_tokens(sim_profile: dict) -> list[str]:
    mcc = sim_profile.get("mcc")
    mnc = sim_profile.get("mnc")
    if not mcc or not mnc:
        return []
    stripped_mnc = str(int(mnc)) if str(mnc).isdigit() else str(mnc)
    tokens = [f"mcc{mcc}-mnc{mnc}"]
    if stripped_mnc != mnc:
        tokens.append(f"mcc{mcc}-mnc{stripped_mnc}")
    return tokens


def check(name: str, ok: bool, expected=None, actual=None, blocker: str | None = None) -> dict:
    return {
        "name": name,
        "ok": ok,
        "expected": expected,
        "actual": actual,
        "blocker": None if ok else blocker or name,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify selected country environment.")
    parser.add_argument("--state-dir", default="~/.global-ug-radar")
    parser.add_argument("--country", required=True, choices=["us", "br", "jp", "kr"])
    parser.add_argument("--countries-config", default=str(SKILL_DIR / "config" / "countries.json"))
    parser.add_argument("--confirm-google-play-country", action="store_true")
    parser.add_argument("--confirm-target-app-country", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()

    countries_config = load_countries(Path(args.countries_config).expanduser())
    profile = countries_config["countries"][args.country]
    sim_profile = profile.get("simProfile") or {}

    devices = adb_devices()
    device_ok = any(device["state"] == "device" for device in devices)

    _, runtime_config_stdout, runtime_config_stderr = adb_shell("am get-config", timeout=10)
    _, timezone_stdout, timezone_stderr = adb_shell("getprop persist.sys.timezone")
    _, locales_stdout, locales_stderr = adb_shell("settings get system system_locales")
    _, persist_locale_stdout, persist_locale_stderr = adb_shell("getprop persist.sys.locale")
    network = host_network_country()

    expected_locale = profile["locale"]
    expected_locale_token = locale_to_config_token(expected_locale)
    actual_locales = " ".join(value for value in [locales_stdout, persist_locale_stdout] if value)
    locale_settings_ok = expected_locale in actual_locales
    runtime_locale_ok = expected_locale_token in runtime_config_stdout
    timezone_ok = timezone_stdout.strip() == profile["timezone"]
    network_ok = network.get("country") == profile["networkCountry"]

    sim_actual = {
        "alpha": getprop("gsm.sim.operator.alpha"),
        "isoCountry": getprop("gsm.sim.operator.iso-country"),
        "numeric": getprop("gsm.sim.operator.numeric"),
    }
    operator_actual = {
        "alpha": getprop("gsm.operator.alpha"),
        "isoCountry": getprop("gsm.operator.iso-country"),
        "numeric": getprop("gsm.operator.numeric"),
    }

    sim_expected = {
        "alpha": sim_profile.get("carrierAlpha"),
        "isoCountry": sim_profile.get("operatorIsoCountry"),
        "numeric": sim_profile.get("operatorNumeric"),
    }
    sim_country_ok = True
    if sim_profile:
        sim_country_ok = (
            sim_actual["isoCountry"] == sim_expected["isoCountry"]
            and sim_actual["numeric"] == sim_expected["numeric"]
        )

    runtime_mcc_mnc_expected = mnc_tokens(sim_profile)
    runtime_mcc_mnc_ok = True
    if runtime_mcc_mnc_expected:
        runtime_mcc_mnc_ok = any(token in runtime_config_stdout for token in runtime_mcc_mnc_expected)

    residual_policy = sim_profile.get("operatorResidualPolicy", "warn")
    operator_country_ok = operator_actual["isoCountry"] == sim_expected.get("isoCountry")
    operator_check_ok = operator_country_ok or residual_policy != "strict"

    warnings = []
    if sim_profile and not operator_country_ok and residual_policy != "strict":
        warnings.append(
            {
                "name": "emulator_radio_operator_residual",
                "actual": operator_actual,
                "note": "Google Play emulator radio registration can remain a built-in virtual US operator; treat Play/app service-side country evidence as the acceptance gate.",
            }
        )
    if locale_settings_ok and not runtime_locale_ok:
        warnings.append(
            {
                "name": "locale_settings_false_positive",
                "actual": {
                    "system_locales": locales_stdout,
                    "persist_sys_locale": persist_locale_stdout,
                    "runtime_config": runtime_config_stdout or runtime_config_stderr,
                },
                "note": "settings system_locales can show the target locale while Android resources still resolve to another language.",
            }
        )

    checks = [
        check("adb_device", device_ok, "device", devices, "device_not_connected"),
        check(
            "runtime_locale",
            runtime_locale_ok,
            expected_locale_token,
            runtime_config_stdout or runtime_config_stderr,
            "country_runtime_locale_mismatch",
        ),
        check(
            "system_locale_setting",
            locale_settings_ok,
            expected_locale,
            actual_locales or f"{locales_stderr} {persist_locale_stderr}".strip(),
            "country_locale_setting_mismatch",
        ),
        check("timezone", timezone_ok, profile["timezone"], timezone_stdout or timezone_stderr, "country_timezone_mismatch"),
        check(
            "runtime_mcc_mnc",
            runtime_mcc_mnc_ok,
            runtime_mcc_mnc_expected or None,
            runtime_config_stdout or runtime_config_stderr,
            "country_runtime_mcc_mnc_mismatch",
        ),
        check("sim_operator", sim_country_ok, sim_expected or None, sim_actual, "country_sim_operator_mismatch"),
        check(
            "emulator_radio_operator",
            operator_check_ok,
            {**sim_expected, "residualPolicy": residual_policy} if sim_expected else None,
            operator_actual,
            "country_radio_operator_mismatch",
        ),
        check(
            "network_country",
            network_ok,
            profile["networkCountry"],
            network,
            "country_network_unavailable" if not network.get("available") else "country_network_mismatch",
        ),
        check("google_play_country_manual", args.confirm_google_play_country, True, args.confirm_google_play_country, "google_play_country_unconfirmed"),
        check("target_app_country_manual", args.confirm_target_app_country, True, args.confirm_target_app_country, "target_app_country_unconfirmed"),
    ]

    blockers = [item["blocker"] for item in checks if not item["ok"]]
    result = {
        "status": "pass" if not blockers else "blocked",
        "country": {
            "id": profile["id"],
            "displayName": profile["displayName"],
            "profileVersion": countries_config.get("profileVersion"),
            "locale": profile["locale"],
            "timezone": profile["timezone"],
            "networkCountry": profile["networkCountry"],
            "recommendedAvdName": profile["recommendedAvdName"],
            "researchAvdName": profile.get("researchAvdName"),
            "playStoreUiSignals": profile.get("playStoreUiSignals", []),
        },
        "checkedAt": datetime.now(timezone.utc).astimezone().isoformat(),
        "checks": checks,
        "warnings": warnings,
        "blockers": blockers,
        "nextSteps": [],
    }

    if "country_network_mismatch" in blockers:
        result["nextSteps"].append("Enable the selected-country VPN/proxy and rerun verification; use the fallback provider details in network_country.actual to diagnose.")
    if "country_network_unavailable" in blockers:
        result["nextSteps"].append("Retry network verification or check VPN/proxy DNS; do not treat a single provider HTTP 429 as proof of country mismatch.")
    if "country_runtime_locale_mismatch" in blockers:
        result["nextSteps"].append("Open Android Language settings and move the selected profile language to the top; settings put system system_locales alone is not sufficient.")
    if "country_locale_setting_mismatch" in blockers or "country_timezone_mismatch" in blockers:
        result["nextSteps"].append("Apply the country profile locale/timezone from references/country-environment.md and rerun verification.")
    if "country_runtime_mcc_mnc_mismatch" in blockers or "country_sim_operator_mismatch" in blockers:
        result["nextSteps"].append("Start the research AVD with the country ICC profile generated by scripts/provision_country_avd.py.")
    if "country_radio_operator_mismatch" in blockers:
        result["nextSteps"].append("Use an emulator profile whose registered radio operator matches the country, or downgrade this to residual risk only after Play/app service-side country evidence is captured.")
    if "google_play_country_unconfirmed" in blockers:
        result["nextSteps"].append("Ask the user to confirm Google Play recommendations/rankings are for the selected country.")
    if "target_app_country_unconfirmed" in blockers:
        result["nextSteps"].append("Ask the user to confirm the target app is showing the selected-country feed/content after login.")

    output = Path(args.output).expanduser() if args.output else Path(args.state_dir).expanduser() / "logs" / f"country-env-{args.country}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
