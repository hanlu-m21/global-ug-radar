#!/usr/bin/env python3
"""Capture the foreground Android app and write a compact evidence summary."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SKILL_DIR = Path(__file__).resolve().parents[1]
REMOTE_XML = "/sdcard/global_ug_window.xml"


def run_command(cmd: list[str], *, text: bool = True, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, check=check, text=text)


def adb_prefix(device: str | None) -> list[str]:
    return ["adb", "-s", device] if device else ["adb"]


def adb_text(device: str | None, *args: str) -> str:
    result = run_command(adb_prefix(device) + list(args), text=True)
    return (result.stdout or result.stderr or "").strip()


def adb_bytes(device: str | None, *args: str) -> bytes:
    result = run_command(adb_prefix(device) + list(args), text=False)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or b"").decode("utf-8", errors="replace"))
    return result.stdout


def default_run_id(country: str) -> str:
    now = datetime.now(timezone.utc).astimezone()
    return f"{now:%Y-%m-%d}-{country}-current-app"


def sanitize_id(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    return value.strip("-") or "current-app"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_focus(window_dump: str) -> tuple[str | None, str | None]:
    patterns = [
        r"mCurrentFocus=.*?\s([A-Za-z0-9_.]+)/(.[^\s}]+|[A-Za-z0-9_.$]+)",
        r"mFocusedApp=.*?\s([A-Za-z0-9_.]+)/(.[^\s}]+|[A-Za-z0-9_.$]+)",
        r"topResumedActivity=.*?\s([A-Za-z0-9_.]+)/(.[^\s}]+|[A-Za-z0-9_.$]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, window_dump)
        if not match:
            continue
        package, activity = match.group(1), match.group(2)
        if activity.startswith("."):
            activity = f"{package}{activity}"
        return package, activity
    return None, None


def package_info(device: str | None, package: str | None) -> dict[str, str | None]:
    if not package:
        return {"packageName": None, "versionName": None, "versionCode": None, "installerPackageName": None}
    dump = adb_text(device, "shell", "dumpsys", "package", package)
    info: dict[str, str | None] = {
        "packageName": package,
        "versionName": None,
        "versionCode": None,
        "installerPackageName": None,
    }
    for key in ["versionName", "versionCode", "installerPackageName"]:
        match = re.search(rf"{key}=([^\s]+)", dump)
        if match:
            info[key] = match.group(1)
    return info


def country_snapshot(device: str | None) -> dict[str, str]:
    return {
        "runtimeConfig": adb_text(device, "shell", "am", "get-config"),
        "systemLocales": adb_text(device, "shell", "settings", "get", "system", "system_locales"),
        "timezone": adb_text(device, "shell", "getprop", "persist.sys.timezone"),
        "simCountry": adb_text(device, "shell", "getprop", "gsm.sim.operator.iso-country"),
        "simOperator": adb_text(device, "shell", "getprop", "gsm.sim.operator.numeric"),
        "networkCountry": adb_text(device, "shell", "getprop", "gsm.operator.iso-country"),
        "networkOperator": adb_text(device, "shell", "getprop", "gsm.operator.numeric"),
    }


def capture_artifacts(device: str | None, route_dir: Path) -> dict[str, str]:
    route_dir.mkdir(parents=True, exist_ok=True)
    screenshot = route_dir / "screen.png"
    hierarchy = route_dir / "screen.xml"
    screenshot.write_bytes(adb_bytes(device, "exec-out", "screencap", "-p"))
    adb_text(device, "shell", "uiautomator", "dump", REMOTE_XML)
    pull = run_command(adb_prefix(device) + ["pull", REMOTE_XML, str(hierarchy)], text=True)
    if pull.returncode != 0:
        raise RuntimeError(pull.stderr.strip())
    return {"screenshot": str(screenshot), "hierarchy": str(hierarchy)}


def node_text(node: ET.Element) -> str:
    parts = []
    for attr in ["text", "content-desc"]:
        value = (node.attrib.get(attr) or "").strip()
        if value:
            parts.append(value)
    return " ".join(parts).strip()


def load_nodes(xml_path: Path) -> list[dict[str, str]]:
    try:
        root = ET.parse(xml_path).getroot()
    except ET.ParseError:
        return []
    nodes = []
    for node in root.iter("node"):
        text = node_text(node)
        if not text:
            continue
        nodes.append(
            {
                "text": text,
                "resourceId": node.attrib.get("resource-id", ""),
                "className": node.attrib.get("class", ""),
                "bounds": node.attrib.get("bounds", ""),
                "clickable": node.attrib.get("clickable", ""),
            }
        )
    return nodes


def contains(text: str, needle: str) -> bool:
    return needle.lower() in text.lower()


def summarize_nodes(
    nodes: list[dict[str, str]],
    signals: dict[str, Any],
    country: str,
    max_texts: int,
    max_candidates: int,
) -> dict[str, Any]:
    country_signals = signals.get("countries", {}).get(country, {})
    high = country_signals.get("highPriorityKeywords", [])
    safe = country_signals.get("safeEntryLabels", [])
    stop = country_signals.get("stopPhrases", [])

    seen_texts: set[str] = set()
    visible_texts: list[str] = []
    candidates: list[dict[str, Any]] = []
    stop_matches: list[dict[str, Any]] = []

    for node in nodes:
        text = node["text"]
        if text not in seen_texts:
            seen_texts.add(text)
            visible_texts.append(text)

        high_matches = [keyword for keyword in high if contains(text, keyword)]
        safe_matches = [label for label in safe if contains(text, label)]
        stop_hits = [phrase for phrase in stop if contains(text, phrase)]

        if stop_hits:
            stop_matches.append({"text": text, "matches": stop_hits, "bounds": node["bounds"]})

        if high_matches or safe_matches:
            candidates.append(
                {
                    "text": text,
                    "score": len(high_matches) * 2 + len(safe_matches) * 3 + (1 if node["clickable"] == "true" else 0),
                    "highPriorityMatches": high_matches,
                    "safeEntryMatches": safe_matches,
                    "clickable": node["clickable"] == "true",
                    "resourceId": node["resourceId"],
                    "className": node["className"],
                    "bounds": node["bounds"],
                }
            )

    candidates.sort(key=lambda item: item["score"], reverse=True)
    return {
        "visibleTexts": visible_texts[:max_texts],
        "visibleTextCount": len(visible_texts),
        "candidateEntries": candidates[:max_candidates],
        "candidateCount": len(candidates),
        "stopMatches": stop_matches[:max_candidates],
        "stopMatchCount": len(stop_matches),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture current Android app and write evidence_summary.json.")
    parser.add_argument("--state-dir", default="~/.global-ug-radar")
    parser.add_argument("--country", required=True, choices=["us", "br", "jp", "kr"])
    parser.add_argument("--run-id")
    parser.add_argument("--app-id", help="Stable app id for the output path. Defaults to foreground package.")
    parser.add_argument("--route-id", default="baseline")
    parser.add_argument("--device")
    parser.add_argument("--countries-config", default=str(SKILL_DIR / "config" / "countries.json"))
    parser.add_argument("--signals-config", default=str(SKILL_DIR / "config" / "ug-signals.json"))
    parser.add_argument("--max-texts", type=int, default=120)
    parser.add_argument("--max-candidates", type=int, default=40)
    args = parser.parse_args()

    run_id = args.run_id or default_run_id(args.country)
    state_dir = Path(args.state_dir).expanduser()

    window_dump = adb_text(args.device, "shell", "dumpsys", "window")
    package, activity = parse_focus(window_dump)
    app_id = sanitize_id(args.app_id or package or "current-app")
    route_dir = state_dir / "runs" / run_id / "apps" / app_id / "routes" / sanitize_id(args.route_id)

    artifacts = capture_artifacts(args.device, route_dir)
    (route_dir / "focus.txt").write_text(window_dump, encoding="utf-8")
    pkg_info = package_info(args.device, package)
    (route_dir / "package.txt").write_text(json.dumps(pkg_info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    signals = load_json(Path(args.signals_config).expanduser())
    countries = load_json(Path(args.countries_config).expanduser())
    nodes = load_nodes(Path(artifacts["hierarchy"]))
    node_summary = summarize_nodes(nodes, signals, args.country, args.max_texts, args.max_candidates)

    summary = {
        "schemaVersion": "2026-05-27.current-app-summary.v1",
        "createdAt": datetime.now(timezone.utc).astimezone().isoformat(),
        "runId": run_id,
        "country": {
            "id": args.country,
            "profileVersion": countries.get("profileVersion"),
            "expected": countries.get("countries", {}).get(args.country, {}),
            "deviceSnapshot": country_snapshot(args.device),
        },
        "app": {
            **pkg_info,
            "foregroundActivity": activity,
            "accountState": "unknown",
        },
        "route": {
            "routeId": args.route_id,
            "sourceType": "native_app_local",
            "status": "captured",
            **artifacts,
        },
        **node_summary,
        "rawArtifactsRetained": True,
        "analysisInstruction": "Use this summary first. Read raw XML/screenshots only if candidates are insufficient or a reportable row cannot be tied to screenshot and route id.",
    }

    output = route_dir / "evidence_summary.json"
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
