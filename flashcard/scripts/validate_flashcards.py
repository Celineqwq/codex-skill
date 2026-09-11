#!/usr/bin/env python3
"""Validate a generated standalone HTML flashcard file."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

DATA_PATTERN = re.compile(
    r'<script\s+id=["\']flashcard-data["\']\s+type=["\']application/json["\']\s*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)
SCRIPT_PATTERN = re.compile(
    r"<script(?P<attrs>[^>]*)>(?P<body>.*?)</script>",
    re.IGNORECASE | re.DOTALL,
)
REQUIRED_IDS = {
    "section-pills",
    "stat-remaining",
    "stat-mastered",
    "stat-review",
    "progress-bar",
    "flashcard",
    "card-front",
    "card-back",
    "previous-btn",
    "forgot-btn",
    "flip-btn",
    "known-btn",
    "shuffle-btn",
    "review-btn",
    "glossary-btn",
    "reset-btn",
    "glossary-modal",
    "word-search",
    "word-list",
}


def validate_shape(document: str) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    match = DATA_PATTERN.search(document)
    if not match:
        return {}, ["missing embedded flashcard JSON block"]

    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError as error:
        return {}, [f"invalid embedded JSON: {error}"]

    if not isinstance(payload, dict):
        errors.append("embedded payload must be an object")
        return {}, errors
    title = payload.get("title")
    cards = payload.get("cards")
    if not isinstance(title, str) or not title.strip():
        errors.append("title must be a non-empty string")
    if not isinstance(cards, list) or not cards:
        errors.append("cards must be a non-empty array")
        return payload, errors

    for index, card in enumerate(cards, 1):
        if not isinstance(card, dict):
            errors.append(f"card {index} must be an object")
            continue
        if not isinstance(card.get("front"), str) or not card["front"].strip():
            errors.append(f"card {index} has an empty front")
        if not isinstance(card.get("back"), str) or not card["back"].strip():
            errors.append(f"card {index} has an empty back")
        if "section" in card and not isinstance(card["section"], str):
            errors.append(f"card {index} section must be a string")
    return payload, errors


def validate_html(document: str) -> list[str]:
    errors: list[str] = []
    for element_id in REQUIRED_IDS:
        if not re.search(rf'id=["\']{re.escape(element_id)}["\']', document):
            errors.append(f"missing element id: {element_id}")
    if "textContent" not in document:
        errors.append("runtime must render card text with textContent")
    if ".innerHTML" in document:
        errors.append("runtime must not assign user content through innerHTML")
    if re.search(r'(?:src|href)=["\']https?://', document, re.IGNORECASE):
        errors.append("output must not reference remote resources")
    return errors


def javascript_sources(document: str) -> list[str]:
    result: list[str] = []
    for match in SCRIPT_PATTERN.finditer(document):
        attrs = match.group("attrs").lower()
        if "application/json" in attrs or "src=" in attrs:
            continue
        if match.group("body").strip():
            result.append(match.group("body"))
    return result


def validate_javascript(document: str) -> list[str]:
    scripts = javascript_sources(document)
    if not scripts:
        return ["missing inline JavaScript"]
    if shutil.which("node") is None:
        return []
    javascript = "\n".join(scripts)
    result = subprocess.run(
        ["node", "--check", "-"],
        input=javascript,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        message = (result.stderr or result.stdout).strip()
        return [f"JavaScript syntax error: {message}"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a standalone HTML flashcard file.")
    parser.add_argument("html_file", type=Path)
    args = parser.parse_args()

    if not args.html_file.is_file():
        print(f"ERROR: file not found: {args.html_file}", file=sys.stderr)
        return 1
    try:
        document = args.html_file.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        print(f"ERROR: file is not UTF-8: {error}", file=sys.stderr)
        return 1

    payload, errors = validate_shape(document)
    errors.extend(validate_html(document))
    errors.extend(validate_javascript(document))
    result = {
        "file": str(args.html_file),
        "valid": not errors,
        "cards": len(payload.get("cards", [])) if isinstance(payload.get("cards"), list) else 0,
        "node_checked": shutil.which("node") is not None,
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
