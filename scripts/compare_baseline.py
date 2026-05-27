#!/usr/bin/env python3
"""Structural baseline comparison for Global UG Radar."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def app_status(current_app: dict, baseline_app: dict | None) -> dict:
    if baseline_app is None:
        return {
            "id": current_app["id"],
            "status": "needs_review",
            "significantChanges": [],
            "reason": "No baseline app record exists.",
        }
    if current_app.get("status") != "captured":
        return {
            "id": current_app["id"],
            "status": current_app.get("status", "not_captured"),
            "significantChanges": [],
            "reason": "Current app was not captured, so no meaningful diff was computed.",
        }
    return {
        "id": current_app["id"],
        "status": "needs_review",
        "significantChanges": [],
        "reason": "Structural comparison complete; visual/OCR/field diff requires captured evidence analysis.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare current prepared JSON to a baseline JSON.")
    parser.add_argument("--current", required=True)
    parser.add_argument("--baseline")
    parser.add_argument("--output")
    args = parser.parse_args()

    current = load_json(Path(args.current).expanduser())
    baseline = load_json(Path(args.baseline).expanduser()) if args.baseline else None
    baseline_apps = {app["id"]: app for app in baseline.get("apps", [])} if baseline else {}
    status = "no_baseline" if baseline is None else "needs_review"
    diff = {
        "runId": current.get("runId"),
        "compareTo": baseline.get("runId", "baseline") if baseline else "baseline",
        "status": status,
        "apps": [app_status(app, baseline_apps.get(app["id"])) for app in current.get("apps", [])],
    }

    output = Path(args.output).expanduser() if args.output else Path(args.current).with_name("diff.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(diff, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
