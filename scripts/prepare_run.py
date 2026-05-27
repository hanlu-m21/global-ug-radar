#!/usr/bin/env python3
"""Create prepared.json for Global UG Radar without fabricating capture data."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def default_run_id() -> str:
    now = datetime.now(timezone.utc).astimezone()
    year, week, _ = now.isocalendar()
    return f"{year}-W{week:02d}"


def build_app_result(app: dict) -> dict:
    source_type = app.get("sourceType", "native_app_local")
    routes = []
    for flow in app.get("flows", []):
        routes.append(
            {
                "routeId": Path(flow).stem,
                "sourceType": source_type,
                "entryPath": [],
                "flow": flow,
                "status": "not_captured",
                "screenshots": [],
                "hierarchy": [],
                "ocr": {"keyTexts": []},
                "ugCandidate": None,
                "safetyConcern": None,
                "notes": "No capture manifest was provided for this route.",
            }
        )
    return {
        "id": app["id"],
        "name": app["name"],
        "packageName": app.get("packageName", "TBD_VERIFY_ON_DEVICE"),
        "appVersion": "TBD",
        "loginState": "unknown",
        "status": "not_captured",
        "sourceType": source_type,
        "discovery": {
            "status": "not_started",
            "artifactsDir": None,
            "confirmedUgPages": 0,
            "blockedCandidates": [],
        },
        "routes": routes,
    }


def apps_for_country(apps_config: dict, country_id: str) -> list[dict]:
    if "countryApps" in apps_config:
        return [
            app
            for app in apps_config.get("countryApps", {}).get(country_id, [])
            if app.get("enabled", True)
        ]
    return [app for app in apps_config.get("apps", []) if app.get("enabled", True)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a prepared run JSON shell.")
    parser.add_argument("--state-dir", default="~/.global-ug-radar")
    parser.add_argument("--country", required=True, choices=["us", "br", "jp", "kr"])
    parser.add_argument("--countries-config", default=str(SKILL_DIR / "config" / "countries.json"))
    parser.add_argument("--apps-config", required=True)
    parser.add_argument("--run-id", default=default_run_id())
    parser.add_argument("--device", default="android-device-or-emulator")
    parser.add_argument("--country-verification-status", default="unknown")
    parser.add_argument("--output", help="Optional explicit output path.")
    args = parser.parse_args()

    countries_config = load_json(Path(args.countries_config).expanduser())
    profile = countries_config["countries"][args.country]
    apps_config = load_json(Path(args.apps_config).expanduser())
    enabled_apps = apps_for_country(apps_config, args.country)

    prepared = {
        "runId": args.run_id,
        "createdAt": datetime.now(timezone.utc).astimezone().isoformat(),
        "environment": {
            "device": args.device,
            "countryId": profile["id"],
            "countryName": profile["displayName"],
            "profileVersion": countries_config.get("profileVersion"),
            "locale": profile["locale"],
            "timezone": profile["timezone"],
            "networkCountry": profile["networkCountry"],
            "countryVerificationStatus": args.country_verification_status,
        },
        "apps": [build_app_result(app) for app in enabled_apps],
    }

    if args.output:
        output = Path(args.output).expanduser()
    else:
        output = Path(args.state_dir).expanduser() / "runs" / args.run_id / "prepared.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(prepared, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
