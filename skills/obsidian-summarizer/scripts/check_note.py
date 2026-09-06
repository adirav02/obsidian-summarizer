#!/usr/bin/env python3
"""Check structural and style signals in an Obsidian Markdown note."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Finding:
    level: str
    code: str
    line: int
    message: str


FENCE_RE = re.compile(r"^\s*(```|~~~)")
CALLOUT_RE = re.compile(r"^\s*>\s*\[!([^\]]+)\]")
IMAGE_MD_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
IMAGE_WIKI_RE = re.compile(r"!\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]")
HEBREW_RE = re.compile(r"[\u0590-\u05FF]")
LATEX_TEXT_RE = re.compile(r"\\(?:text|textrm|textbf|textit)\s*\{([^{}]*)\}")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def parse_simple_yaml(path: Path | None) -> dict[str, object]:
    """Parse the small profile subset without adding a YAML dependency."""
    if path is None:
        return {}
    result: dict[str, object] = {}
    section: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip() or ":" not in line:
            continue
        indent = len(line) - len(line.lstrip())
        key, value = (part.strip() for part in line.split(":", 1))
        if indent == 0:
            section = key if not value else None
            if value:
                result[key] = value.strip("\"'")
        elif section and value:
            result[f"{section}.{key}"] = value.strip("\"'")
    return result


def is_external(target: str) -> bool:
    return bool(re.match(r"^(?:https?://|data:|mailto:)", target))


def clean_target(target: str) -> str:
    target = target.strip().strip("<>").split("#", 1)[0]
    if " " in target and not target.startswith("/"):
        possible_path, possible_title = target.rsplit(" ", 1)
        if possible_title.startswith(('"', "'")):
            target = possible_path
    return target


def check_note(path: Path, profile: dict[str, object] | None = None) -> list[Finding]:
    profile = profile or {}
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    findings: list[Finding] = []
    in_fence = False
    fence_marker = ""
    in_math = False
    headings: list[tuple[int, str]] = []

    for number, line in enumerate(lines, start=1):
        fence = FENCE_RE.match(line)
        if fence:
            marker = fence.group(1)
            if not in_fence:
                in_fence, fence_marker = True, marker
            elif marker == fence_marker:
                in_fence, fence_marker = False, ""
            continue

        if in_fence:
            continue

        if line.strip() == "$$":
            in_math = not in_math
            continue

        heading = HEADING_RE.match(line)
        if heading:
            headings.append((len(heading.group(1)), heading.group(2)))

        if line.lstrip().startswith(">") and "[!" in line:
            match = CALLOUT_RE.match(line)
            if not match or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*[+-]?", match.group(1)):
                findings.append(Finding("error", "invalid-callout", number, "Malformed Obsidian callout marker"))

        prose = not in_math and not line.lstrip().startswith(("|", ">", "<!--"))
        if prose and ";" in line and profile.get("punctuation.semicolons_in_prose") in {"avoid", "forbid"}:
            findings.append(Finding("warning", "semicolon-prose", number, "Semicolon found in generated prose"))
        if prose and "—" in line and profile.get("punctuation.em_dash") == "replace_with_hyphen":
            findings.append(Finding("warning", "em-dash", number, "Em dash found where the profile prefers a hyphen"))

        for match in LATEX_TEXT_RE.finditer(line):
            if HEBREW_RE.search(match.group(1)):
                findings.append(Finding("error", "rtl-in-latex-text", number, "RTL text found inside a LaTeX text command"))

        for pattern in (IMAGE_MD_RE, IMAGE_WIKI_RE):
            for match in pattern.finditer(line):
                target = clean_target(match.group(1))
                if not target or is_external(target):
                    continue
                candidate = (path.parent / target).resolve()
                if not candidate.exists():
                    findings.append(Finding("error", "missing-image", number, f"Local image does not exist: {target}"))

    if in_fence:
        findings.append(Finding("error", "unclosed-fence", len(lines), "Code fence is not closed"))
    if in_math:
        findings.append(Finding("error", "unclosed-display-math", len(lines), "Display math block is not closed"))

    previous_level = 0
    for level, title in headings:
        if previous_level and level > previous_level + 1:
            line_no = next(i for i, value in enumerate(lines, 1) if value.lstrip().startswith("#" * level + " ") and title in value)
            findings.append(Finding("warning", "heading-jump", line_no, f"Heading jumps from H{previous_level} to H{level}"))
        previous_level = level

    check_tables(lines, findings)
    check_learning_sections(headings, profile, findings)
    return sorted(findings, key=lambda item: (item.line, item.level, item.code))


def split_table_row(line: str) -> list[str]:
    stripped = line.strip().strip("|")
    return re.split(r"(?<!\\)\|", stripped)


def check_tables(lines: list[str], findings: list[Finding]) -> None:
    index = 0
    while index < len(lines) - 1:
        if "|" not in lines[index] or not re.fullmatch(r"\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*", lines[index + 1]):
            index += 1
            continue
        expected = len(split_table_row(lines[index]))
        cursor = index + 2
        while cursor < len(lines) and "|" in lines[cursor] and lines[cursor].strip():
            actual = len(split_table_row(lines[cursor]))
            if actual != expected:
                findings.append(Finding("error", "table-width", cursor + 1, f"Table row has {actual} cells, expected {expected}"))
            cursor += 1
        index = cursor


def check_learning_sections(headings: list[tuple[int, str]], profile: dict[str, object], findings: list[Finding]) -> None:
    titles = " ".join(title.casefold() for _, title in headings)
    requested = {
        "glossary": ("glossary", "מילון מושגים"),
        "one_sentence_takeaway": ("one-sentence takeaway", "one sentence takeaway", "סיכום במשפט אחד"),
        "common_mistakes": ("common mistake", "common mistakes", "טעויות נפוצות"),
    }
    for key, aliases in requested.items():
        value = str(profile.get(key, "")).casefold()
        required = value == "true" or (key == "common_mistakes" and value == "true")
        if required and not any(alias in titles for alias in aliases):
            findings.append(Finding("warning", f"missing-{key.replace('_', '-')}", 1, f"Profile requests a {key.replace('_', ' ')} section"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("note", type=Path)
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--strict", action="store_true", help="Return nonzero for warnings as well as errors")
    args = parser.parse_args(argv)

    if not args.note.is_file():
        parser.error(f"note does not exist: {args.note}")
    if args.profile and not args.profile.is_file():
        parser.error(f"profile does not exist: {args.profile}")

    findings = check_note(args.note, parse_simple_yaml(args.profile))
    if args.as_json:
        print(json.dumps([asdict(item) for item in findings], ensure_ascii=False, indent=2))
    elif findings:
        for item in findings:
            print(f"{item.level.upper():7} {item.code:28} line {item.line}: {item.message}")
    else:
        print("OK: no structural or configured-style issues found")

    has_errors = any(item.level == "error" for item in findings)
    return 1 if has_errors or (args.strict and findings) else 0


if __name__ == "__main__":
    sys.exit(main())
