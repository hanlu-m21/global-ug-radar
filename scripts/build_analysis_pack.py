#!/usr/bin/env python3
"""Build a compact analysis pack from captured evidence summaries."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path | None) -> str | None:
    if not path or not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def summarize_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "text": candidate.get("text"),
        "score": candidate.get("score"),
        "highPriorityMatches": candidate.get("highPriorityMatches", []),
        "safeEntryMatches": candidate.get("safeEntryMatches", []),
        "clickable": bool(candidate.get("clickable")),
        "resourceId": candidate.get("resourceId", ""),
        "bounds": candidate.get("bounds", ""),
    }


def fallback_reasons(summary: dict[str, Any], min_visible_texts: int) -> list[str]:
    reasons: list[str] = []
    route = summary.get("route", {})
    if not route.get("screenshot") or not route.get("hierarchy"):
        reasons.append("missing_raw_artifact_path")
    if int(summary.get("visibleTextCount") or 0) < min_visible_texts:
        reasons.append("too_few_visible_texts")
    if int(summary.get("candidateCount") or 0) == 0:
        reasons.append("no_candidate_entries")
    if summary.get("stopMatchCount"):
        reasons.append("safety_stop_phrase_present")
    if not summary.get("app", {}).get("packageName"):
        reasons.append("missing_package_identity")
    return reasons


def route_card(path: Path, summary: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    route = summary.get("route", {})
    screenshot = Path(route["screenshot"]).expanduser() if route.get("screenshot") else None
    hierarchy = Path(route["hierarchy"]).expanduser() if route.get("hierarchy") else None
    country = summary.get("country", {})
    app = summary.get("app", {})
    candidates = summary.get("candidateEntries", [])[: args.max_candidates]
    reasons = fallback_reasons(summary, args.min_visible_texts)

    return {
        "summaryPath": str(path),
        "routeKey": f"{app.get('packageName') or 'unknown'}:{route.get('routeId') or path.parent.name}",
        "country": {
            "id": country.get("id"),
            "profileVersion": country.get("profileVersion"),
            "deviceSnapshot": country.get("deviceSnapshot", {}),
        },
        "app": {
            "packageName": app.get("packageName"),
            "versionName": app.get("versionName"),
            "versionCode": app.get("versionCode"),
            "foregroundActivity": app.get("foregroundActivity"),
            "accountState": app.get("accountState"),
        },
        "route": {
            "routeId": route.get("routeId"),
            "sourceType": route.get("sourceType"),
            "status": route.get("status"),
            "screenshot": route.get("screenshot"),
            "hierarchy": route.get("hierarchy"),
        },
        "visibleTexts": summary.get("visibleTexts", [])[: args.max_texts],
        "visibleTextCount": summary.get("visibleTextCount", 0),
        "candidateEntries": [summarize_candidate(candidate) for candidate in candidates],
        "candidateCount": summary.get("candidateCount", 0),
        "stopMatches": summary.get("stopMatches", []),
        "stopMatchCount": summary.get("stopMatchCount", 0),
        "evidenceHash": {
            "screenshotSha256": sha256_file(screenshot),
            "hierarchySha256": sha256_file(hierarchy),
            "summarySha256": sha256_file(path),
        },
        "rawFallback": {
            "required": bool(reasons),
            "reasons": reasons,
        },
    }


def build_pack(args: argparse.Namespace) -> dict[str, Any]:
    run_dir = Path(args.state_dir).expanduser() / "runs" / args.run_id
    summaries = sorted(run_dir.glob("apps/*/routes/*/evidence_summary.json"))
    if not summaries:
        raise SystemExit(f"no evidence_summary.json files found under {run_dir}")
    cards = [route_card(path, load_json(path), args) for path in summaries]
    fallback_cards = [card for card in cards if card["rawFallback"]["required"]]

    return {
        "schemaVersion": "2026-05-27.analysis-pack.v1",
        "createdAt": datetime.now(timezone.utc).astimezone().isoformat(),
        "runId": args.run_id,
        "mode": "standard_raw_fallback",
        "qualityContract": {
            "evidenceCapture": "full_raw_artifacts_retained",
            "defaultModelInput": "analysis_pack.json",
            "rawFallback": "read screenshots/XML/OCR when the pack is insufficient, conflicting, or cannot bind a row to route evidence",
            "estimatedTokenSavings": "45-65%",
            "targetQualityLoss": "0-2%",
        },
        "summary": {
            "routeCount": len(cards),
            "candidateEntryCount": sum(int(card.get("candidateCount") or 0) for card in cards),
            "rawFallbackRouteCount": len(fallback_cards),
        },
        "routeCards": cards,
        "rawFallbackRequired": [
            {
                "routeKey": card["routeKey"],
                "summaryPath": card["summaryPath"],
                "reasons": card["rawFallback"]["reasons"],
                "screenshot": card["route"].get("screenshot"),
                "hierarchy": card["route"].get("hierarchy"),
            }
            for card in fallback_cards
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build token-efficient analysis_pack.json from evidence summaries.")
    parser.add_argument("--state-dir", default="~/.global-ug-radar")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output")
    parser.add_argument("--max-texts", type=int, default=40)
    parser.add_argument("--max-candidates", type=int, default=12)
    parser.add_argument("--min-visible-texts", type=int, default=5)
    args = parser.parse_args()

    pack = build_pack(args)
    output = Path(args.output).expanduser() if args.output else Path(args.state_dir).expanduser() / "runs" / args.run_id / "analysis_pack.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
