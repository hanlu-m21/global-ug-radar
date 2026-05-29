#!/usr/bin/env python3
"""Render Global UG Radar findings JSON into fixed 5-column Feishu XML."""

from __future__ import annotations

import argparse
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


GOALS = {
    "任务转化",
    "用户分层",
    "提升参与意愿",
    "促活留存",
    "付费转化",
    "拉新裂变",
    "品牌建设",
    "投稿激励",
    "分享传播",
}


def text_len(value: str) -> int:
    return len(value.strip())


def escape_inline(value: str) -> str:
    escaped = html.escape(value.strip(), quote=False)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)


def cell(lines: list[str] | str) -> str:
    if isinstance(lines, str):
        body = escape_inline(lines)
    else:
        body = "<br/>".join(escape_inline(line) for line in lines if str(line).strip())
    return f"<td>{body}</td>"


def normalize_screenshot_entries(value: Any, row_id: str | None = None) -> list[dict[str, str]]:
    if isinstance(value, str):
        return [{"path": value, "label": value}]
    if not isinstance(value, list):
        raise ValueError("screenshots must be a string or list")
    entries = []
    for item in value:
        if isinstance(item, str):
            entries.append({"path": item, "label": item})
        elif isinstance(item, dict):
            path = item.get("path") or item.get("src") or item.get("file") or ""
            label = item.get("label") or item.get("caption") or item.get("state") or path
            if label or path:
                entry = {"path": str(path), "label": str(label or path)}
                if item.get("id"):
                    entry["id"] = str(item["id"])
                if row_id:
                    entry["rowId"] = row_id
                entries.append(entry)
        else:
            raise ValueError("screenshots entries must be strings or objects")
    return entries


def normalize_screenshots(value: Any) -> list[str]:
    return [entry["label"] for entry in normalize_screenshot_entries(value)]


def validate(data: dict[str, Any]) -> None:
    product_name = str(data.get("productName", "")).strip()
    product_intro = str(data.get("productIntro", "")).strip()
    rows = data.get("rows")
    if not product_name:
        raise ValueError("productName is required")
    if not product_intro:
        raise ValueError("productIntro is required")
    if text_len(product_intro) > 80:
        raise ValueError("productIntro must be <= 80 characters")
    if not isinstance(rows, list) or not rows:
        raise ValueError("rows must be a non-empty list")

    for index, row in enumerate(rows, start=1):
        row_id = str(row.get("rowId", "")).strip()
        one_line = str(row.get("oneLine", "")).strip()
        goal = str(row.get("goal", "")).strip()
        highlights = row.get("highlights")
        takeaway = str(row.get("takeaway", "")).strip()
        screenshots = normalize_screenshots(row.get("screenshots"))

        if not row_id:
            raise ValueError(f"row {index}: rowId is required")
        if not re.match(r"^[A-Za-z0-9_.-]+$", row_id):
            raise ValueError(f"row {index}: rowId must contain only letters, digits, dot, underscore, or hyphen")
        if not one_line:
            raise ValueError(f"row {index}: oneLine is required")
        if text_len(one_line) > 15:
            raise ValueError(f"row {index}: oneLine must be <= 15 characters")
        if not screenshots:
            raise ValueError(f"row {index}: screenshots are required")
        if len(screenshots) > 3:
            raise ValueError(f"row {index}: screenshots must contain 1-3 entries")
        if goal not in GOALS:
            raise ValueError(f"row {index}: goal must be one of {sorted(GOALS)}")
        if not isinstance(highlights, list) or not highlights:
            raise ValueError(f"row {index}: highlights must be a non-empty list")
        if len(highlights) > 6:
            raise ValueError(f"row {index}: highlights must contain at most 6 items")
        for item in highlights:
            if text_len(str(item)) > 70:
                raise ValueError(f"row {index}: each highlight must be <= 70 characters")
        if text_len(takeaway) > 80:
            raise ValueError(f"row {index}: takeaway must be <= 80 characters")


def numbered(items: list[Any]) -> list[str]:
    return [f"{index}. {str(item).strip()}" for index, item in enumerate(items, start=1)]


def build_image_manifest(data: dict[str, Any], title: str | None, require_local_images: bool) -> dict[str, Any]:
    validate(data)
    rows = []
    for row_index, row in enumerate(data["rows"], start=4):
        row_id = str(row["rowId"]).strip()
        screenshots = []
        for image_index, entry in enumerate(normalize_screenshot_entries(row["screenshots"], row_id), start=1):
            path = entry.get("path", "").strip()
            exists = bool(path and Path(path).expanduser().is_file())
            if require_local_images and not exists:
                raise ValueError(f"{row_id} screenshot {image_index}: local image path is missing or unreadable: {path}")
            screenshots.append(
                {
                    "imageIndex": image_index,
                    "label": entry.get("label", ""),
                    "path": path,
                    "placeholder": f"{{{{screenshot:{row_id}:{image_index}}}}}",
                    "localFileExists": exists,
                }
            )
        rows.append(
            {
                "rowId": row_id,
                "tableRowIndex": row_index,
                "screenshotCell": {
                    "columnName": "玩法截图",
                    "columnIndex": 2,
                },
                "screenshots": screenshots,
            }
        )
    return {
        "schemaVersion": "2026-05-27.feishu-table-images.v1",
        "createdAt": datetime.now(timezone.utc).astimezone().isoformat(),
        "title": title,
        "productName": str(data["productName"]).strip(),
        "tableShape": {
            "columns": ["一句话介绍", "玩法截图", "目标", "亮点分析", "可借鉴点"],
            "screenshotColumnIndex": 2,
            "gameplayStartRowIndex": 4,
        },
        "rows": rows,
    }


def render(data: dict[str, Any], title: str | None) -> str:
    validate(data)
    product_name = str(data["productName"]).strip()
    product_intro = str(data["productIntro"]).strip()
    rows = data["rows"]

    parts: list[str] = []
    if title:
        parts.append(f"<h2>{escape_inline(title)}</h2>")
    parts.append("<table>")
    parts.append("  <tbody>")
    parts.append(f"    <tr>{cell('产品名称')}<td colspan=\"4\">{escape_inline(product_name)}</td></tr>")
    parts.append(f"    <tr>{cell('产品介绍')}<td colspan=\"4\">{escape_inline(product_intro)}</td></tr>")
    parts.append(f"    <tr>{cell('一句话介绍')}{cell('玩法截图')}{cell('目标')}{cell('亮点分析')}{cell('可借鉴点')}</tr>")
    for row in rows:
        parts.append("    <tr>")
        parts.append(f"      {cell(str(row['oneLine']))}")
        parts.append(f"      {cell(normalize_screenshots(row['screenshots']))}")
        parts.append(f"      {cell(str(row['goal']))}")
        parts.append(f"      {cell(numbered(row['highlights']))}")
        parts.append(f"      {cell(str(row['takeaway']))}")
        parts.append("    </tr>")
    parts.append("  </tbody>")
    parts.append("</table>")
    return "\n".join(parts) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render fixed 5-column Feishu table XML from findings JSON.")
    parser.add_argument("--input", required=True, help="Findings JSON path.")
    parser.add_argument("--output", help="Output XML path. Defaults to stdout.")
    parser.add_argument("--title", help="Optional h2 title above the table.")
    parser.add_argument("--image-manifest-output", help="Output JSON manifest mapping screenshots to table cells.")
    parser.add_argument("--require-local-images", action="store_true", help="Fail if any screenshot path is missing or unreadable.")
    args = parser.parse_args()

    data = json.loads(Path(args.input).expanduser().read_text(encoding="utf-8"))
    xml = render(data, args.title)
    if args.image_manifest_output:
        manifest = build_image_manifest(data, args.title, args.require_local_images)
        manifest_output = Path(args.image_manifest_output).expanduser()
        manifest_output.parent.mkdir(parents=True, exist_ok=True)
        manifest_output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.output:
        output = Path(args.output).expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(xml, encoding="utf-8")
        print(output)
    else:
        print(xml, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
