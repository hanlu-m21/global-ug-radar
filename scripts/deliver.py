#!/usr/bin/env python3
"""Build Feishu delivery payloads for Global UG Radar."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def read_text_if_exists(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def load_json_if_exists(path: Path | None) -> dict[str, Any] | None:
    if not path or not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def detect_image_format(path: Path) -> str | None:
    header = path.read_bytes()[:16]
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if header.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if header[:6] in {b"GIF87a", b"GIF89a"}:
        return ".gif"
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return ".webp"
    return None


def manifest_from_findings(data: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for row_index, row in enumerate(data.get("rows", []), start=4):
        row_id = str(row.get("rowId") or f"row-{row_index - 3}")
        screenshots = []
        raw_screenshots = row.get("screenshots", [])
        if isinstance(raw_screenshots, str):
            raw_screenshots = [raw_screenshots]
        if not isinstance(raw_screenshots, list):
            raw_screenshots = []
        for image_index, item in enumerate(raw_screenshots, start=1):
            if isinstance(item, str):
                path = item
                label = item
            elif isinstance(item, dict):
                path = str(item.get("path") or item.get("src") or item.get("file") or "")
                label = str(item.get("label") or item.get("caption") or item.get("state") or path)
            else:
                path = ""
                label = ""
            screenshots.append(
                {
                    "imageIndex": image_index,
                    "label": label,
                    "path": path,
                    "placeholder": f"{{{{screenshot:{row_id}:{image_index}}}}}",
                }
            )
        rows.append(
            {
                "rowId": row_id,
                "tableRowIndex": row_index,
                "screenshotCell": {"columnName": "玩法截图", "columnIndex": 2},
                "screenshots": screenshots,
            }
        )
    return {
        "schemaVersion": "2026-05-27.feishu-table-images.v1",
        "productName": data.get("productName"),
        "rows": rows,
    }


def strict_image_preflight(manifest: dict[str, Any], max_image_bytes: int) -> dict[str, Any]:
    checked = []
    errors = []
    for row in manifest.get("rows", []):
        row_id = row.get("rowId")
        screenshot_cell = row.get("screenshotCell", {})
        if screenshot_cell.get("columnName") != "玩法截图" or screenshot_cell.get("columnIndex") != 2:
            errors.append(f"{row_id}: screenshot cell must be column 2 / 玩法截图")
        for screenshot in row.get("screenshots", []):
            raw_path = str(screenshot.get("path") or "").strip()
            if not raw_path:
                errors.append(f"{row_id}: screenshot {screenshot.get('imageIndex')} has no local path")
                continue
            path = Path(raw_path).expanduser()
            if not path.exists() or not path.is_file():
                errors.append(f"{row_id}: screenshot path is missing or not a file: {path}")
                continue
            suffix = path.suffix.lower()
            if suffix not in SUPPORTED_IMAGE_SUFFIXES:
                errors.append(f"{row_id}: unsupported screenshot format {suffix}: {path}")
                continue
            detected_format = detect_image_format(path)
            if not detected_format:
                errors.append(f"{row_id}: screenshot file header is not a supported image: {path}")
                continue
            size = path.stat().st_size
            if size <= 0:
                errors.append(f"{row_id}: screenshot is empty: {path}")
                continue
            if size > max_image_bytes:
                errors.append(f"{row_id}: screenshot exceeds max bytes ({size} > {max_image_bytes}): {path}")
                continue
            checked.append(
                {
                    "rowId": row_id,
                    "tableRowIndex": row.get("tableRowIndex"),
                    "screenshotColumnIndex": 2,
                    "imageIndex": screenshot.get("imageIndex"),
                    "label": screenshot.get("label", ""),
                    "path": str(path),
                    "detectedFormat": detected_format,
                    "bytes": size,
                    "sha256": sha256_file(path),
                }
            )
    if errors:
        raise SystemExit("image_preflight_failed:\n" + "\n".join(f"- {error}" for error in errors))
    return {
        "status": "pass",
        "checkedCount": len(checked),
        "images": checked,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a Feishu payload JSON. Sending is opt-in only.")
    parser.add_argument("--state-dir", default="~/.global-ug-radar")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--analysis")
    parser.add_argument("--findings-json", help="Structured findings JSON used to derive strict table image placement.")
    parser.add_argument("--table-manifest", help="Manifest generated by render_feishu_table.py --image-manifest-output.")
    parser.add_argument("--feishu-config", default="config/feishu.example.json")
    parser.add_argument("--output")
    parser.add_argument("--dry-run", action="store_true", help="Never send. This is the default behavior.")
    parser.add_argument("--send", action="store_true", help="Reserved for future explicit Feishu sending.")
    parser.add_argument("--strict-table-images", action="store_true", help="Fail before payload creation unless every screenshot is mapped to the 玩法截图 cell and is locally readable.")
    parser.add_argument("--max-image-bytes", type=int, default=10 * 1024 * 1024)
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

    table_manifest = load_json_if_exists(Path(args.table_manifest).expanduser() if args.table_manifest else None)
    findings = load_json_if_exists(Path(args.findings_json).expanduser() if args.findings_json else None)
    if not table_manifest and findings:
        table_manifest = manifest_from_findings(findings)
    image_preflight = None
    if args.strict_table_images:
        if not table_manifest:
            raise SystemExit("--strict-table-images requires --table-manifest or --findings-json")
        image_preflight = strict_image_preflight(table_manifest, args.max_image_bytes)

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
            "strictTableImages": bool(args.strict_table_images),
            "tableImageManifest": table_manifest,
            "imagePreflight": image_preflight,
        },
    }

    output = Path(args.output).expanduser() if args.output else run_dir / "feishu-payload.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
