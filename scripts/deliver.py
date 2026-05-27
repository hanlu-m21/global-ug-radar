#!/usr/bin/env python3
"""Build Feishu delivery payloads for Global UG Radar."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def read_text_if_exists(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a Feishu payload JSON. Sending is opt-in only.")
    parser.add_argument("--state-dir", default="~/.global-ug-radar")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--analysis")
    parser.add_argument("--feishu-config", default="config/feishu.example.json")
    parser.add_argument("--output")
    parser.add_argument("--dry-run", action="store_true", help="Never send. This is the default behavior.")
    parser.add_argument("--send", action="store_true", help="Reserved for future explicit Feishu sending.")
    args = parser.parse_args()

    if args.send:
        raise SystemExit("Sending is not implemented in Phase 1. Generate payload locally and confirm Feishu path first.")

    state_dir = Path(args.state_dir).expanduser()
    run_dir = state_dir / "runs" / args.run_id
    analysis_path = Path(args.analysis).expanduser() if args.analysis else run_dir / "analysis.md"
    feishu_config_path = Path(args.feishu_config).expanduser()
    config = {}
    if feishu_config_path.exists():
        config = json.loads(feishu_config_path.read_text(encoding="utf-8"))

    payload = {
        "runId": args.run_id,
        "createdAt": datetime.now(timezone.utc).astimezone().isoformat(),
        "dryRun": True,
        "feishu": config.get("feishu", {}),
        "message": {
            "title": f"全球 UG 竞品巡检｜{args.run_id}",
            "body": read_text_if_exists(analysis_path) or "本次运行尚未生成 analysis.md。",
        },
        "docAppend": {
            "enabled": False,
            "reason": "Phase 1 only creates local payloads until Feishu write mode is confirmed.",
        },
    }

    output = Path(args.output).expanduser() if args.output else run_dir / "feishu-payload.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
