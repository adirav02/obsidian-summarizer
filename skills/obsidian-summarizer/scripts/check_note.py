#!/usr/bin/env python3
"""Check structural and configured style signals in an Obsidian Markdown note."""

from __future__ import annotations

import argparse
import bisect
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Finding:
    level: str
    code: str
    line: int
    message: str


FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
CALLOUT_RE = re.compile(r"^\[!([^\]]+)\](?:[+-])?(?:\s+.*)?$")
IMAGE_MD_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
IMAGE_WIKI_RE = re.compile(r"!\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
INLINE_CODE_RE = re.compile(r"(`+)(.*?)(?<!`)\1(?!`)")
URL_RE = re.compile(r"(?:https?://|mailto:)[^\s)>]+")
ENTITY_RE = re.compile(r"&(?:#\d+|#x[0-9A-Fa-f]+|[A-Za-z][A-Za-z0-9]+);")
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[([^\]]*)\]\((?:<[^>]+>|[^)]*)\)")
WIKILINK_RE = re.compile(r"!?\[\[[^\]]+\]\]")
HIGHLIGHT_RE = re.compile(r"==[^=\n]+==")

# Strong signals of natural-language text, not a blanket Unicode ban. Greek is
# deliberately excluded because individual Greek letters are ordinary math symbols.
NON_ENGLISH_SCRIPT_RE = re.compile(
    "["
    "\u0590-\u05ff"
    "\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff"
    "\u0400-\u052f"
    "\u0530-\u058f"
    "\u0900-\u097f"
    "\u10a0-\u10ff"
    "\u3040-\u30ff"
    "\u3400-\u4dbf\u4e00-\u9fff"
    "\uac00-\ud7af"
    "]"
)


def _parse_scalar(value: str) -> object:
    value = value.strip()
    if not value:
        return ""
    if value.startswith("[") and value.endswith("]"):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass
    lowered = value.casefold()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none", "~"}:
        return None
    return value.strip("\"'")


def parse_simple_yaml(path: Path | None) -> dict[str, object]:
    """Parse the profiles' scalar and inline-list YAML subset into dotted keys."""
    if path is None:
        return {}
    result: dict[str, object] = {}
    parents: list[tuple[int, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip() or ":" not in line:
            continue
        indent = len(line) - len(line.lstrip(" "))
        key, value = (part.strip() for part in line.split(":", 1))
        while parents and parents[-1][0] >= indent:
            parents.pop()
        dotted = ".".join([parent for _, parent in parents] + [key])
        if value:
            result[dotted] = _parse_scalar(value)
        else:
            parents.append((indent, key))
    return result


def apply_overrides(profile: dict[str, object], overrides: Iterable[str]) -> dict[str, object]:
    """Overlay request-specific dotted-key assignments on an effective profile."""
    merged = dict(profile)
    for assignment in overrides:
        if "=" not in assignment:
            raise ValueError(f"override must use KEY=VALUE: {assignment}")
        key, value = assignment.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"override key is empty: {assignment}")
        merged[key] = _parse_scalar(value)
    return merged


def load_effective_profile(
    selected_profile: Path | None = None,
    overrides: Iterable[str] = (),
    default_profile: Path | None = None,
) -> dict[str, object]:
    """Load defaults, then a selected profile, then request-specific overrides."""
    if default_profile is None:
        default_profile = Path(__file__).parents[1] / "profiles" / "default.yaml"
    merged = parse_simple_yaml(default_profile)
    if selected_profile is not None and selected_profile.resolve() != default_profile.resolve():
        merged.update(parse_simple_yaml(selected_profile))
    return apply_overrides(merged, overrides)


def is_external(target: str) -> bool:
    return bool(re.match(r"^(?:https?://|data:|mailto:)", target))


def clean_target(target: str) -> str:
    target = target.strip().strip("<>").split("#", 1)[0]
    if " " in target and not target.startswith("/"):
        possible_path, possible_title = target.rsplit(" ", 1)
        if possible_title.startswith(('"', "'")):
            target = possible_path
    return target


def strip_blockquote_prefix(line: str) -> tuple[str, bool]:
    """Remove one or more Markdown blockquote prefixes, including callout bodies."""
    quoted = False
    remaining = line
    while True:
        match = re.match(r"^\s*>\s?", remaining)
        if not match:
            return remaining, quoted
        quoted = True
        remaining = remaining[match.end() :]


def mask_inline_code(line: str) -> str:
    previous = None
    while previous != line:
        previous = line
        line = INLINE_CODE_RE.sub(lambda match: " " * len(match.group(0)), line)
    return line


def _is_escaped(text: str, index: int) -> bool:
    backslashes = 0
    cursor = index - 1
    while cursor >= 0 and text[cursor] == "\\":
        backslashes += 1
        cursor -= 1
    return backslashes % 2 == 1


def find_math_spans(lines: list[str | None]) -> tuple[list[tuple[int, str]], str | None]:
    """Return inline/display math spans after fenced and inline code have been masked."""
    text = "\n".join("" if line is None else mask_inline_code(line) for line in lines)
    newline_offsets = [index for index, char in enumerate(text) if char == "\n"]
    spans: list[tuple[int, str]] = []
    delimiter: str | None = None
    content_start = 0
    opening_index = 0
    index = 0
    while index < len(text):
        if text[index] != "$" or _is_escaped(text, index):
            index += 1
            continue
        token = "$$" if text.startswith("$$", index) else "$"
        if delimiter is None:
            delimiter = token
            opening_index = index
            content_start = index + len(token)
            index = content_start
        elif token == delimiter:
            line = bisect.bisect_right(newline_offsets, opening_index) + 1
            spans.append((line, text[content_start:index]))
            delimiter = None
            index += len(token)
        else:
            index += len(token)
    return spans, delimiter


def mask_math_for_prose(line: str, in_display: bool) -> tuple[str, bool]:
    chars = list(line)
    index = 0
    inline = False
    while index < len(line):
        if line[index] != "$" or _is_escaped(line, index):
            if in_display or inline:
                chars[index] = " "
            index += 1
            continue
        token_length = 2 if line.startswith("$$", index) else 1
        if token_length == 2:
            chars[index : index + 2] = [" ", " "]
            in_display = not in_display
            index += 2
        elif not in_display:
            chars[index] = " "
            inline = not inline
            index += 1
        else:
            chars[index] = " "
            index += 1
    return "".join(chars), in_display


def _enabled(value: object) -> bool:
    return value is True or str(value).casefold() == "true"


def check_note(path: Path, profile: dict[str, object] | None = None) -> list[Finding]:
    profile = profile or {}
    lines = path.read_text(encoding="utf-8").splitlines()
    findings: list[Finding] = []
    in_fence = False
    fence_marker = ""
    headings: list[tuple[int, int, str]] = []
    content_lines: list[str | None] = []
    prose_math_state = False
    in_frontmatter = bool(lines and lines[0].strip() == "---")
    in_callout = False

    for number, original_line in enumerate(lines, start=1):
        if in_frontmatter:
            content_lines.append(None)
            if number > 1 and original_line.strip() == "---":
                in_frontmatter = False
            continue
        normalized, quoted = strip_blockquote_prefix(original_line)
        if not quoted:
            in_callout = False
        fence = FENCE_RE.match(normalized)
        if fence:
            marker = fence.group(1)
            if not in_fence:
                in_fence, fence_marker = True, marker[0]
            elif marker[0] == fence_marker:
                in_fence, fence_marker = False, ""
            content_lines.append(None)
            continue
        if in_fence:
            content_lines.append(None)
            continue

        content_lines.append(normalized)
        heading = HEADING_RE.match(original_line)
        if heading:
            headings.append((number, len(heading.group(1)), heading.group(2)))

        if quoted and normalized.lstrip().startswith("[!"):
            marker_text = normalized.strip()
            match = CALLOUT_RE.fullmatch(marker_text)
            if not match or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", match.group(1)):
                findings.append(Finding("error", "invalid-callout", number, "Malformed Obsidian callout marker"))
                in_callout = False
            else:
                in_callout = True

        if in_callout and HIGHLIGHT_RE.search(mask_inline_code(normalized)):
            findings.append(
                Finding(
                    "error",
                    "highlight-in-callout",
                    number,
                    "Obsidian highlight markup is not allowed inside callouts",
                )
            )

        prose = mask_inline_code(normalized)
        prose, prose_math_state = mask_math_for_prose(prose, prose_math_state)
        prose = URL_RE.sub("", prose)
        prose = ENTITY_RE.sub("", prose)
        prose = MARKDOWN_LINK_RE.sub(lambda match: match.group(1), prose)
        prose = WIKILINK_RE.sub("", prose)
        is_prose = not prose.lstrip().startswith(("|", "<!--", "[!"))
        if is_prose and ";" in prose and profile.get("punctuation.semicolons_in_prose") in {"avoid", "forbid"}:
            findings.append(Finding("warning", "semicolon-prose", number, "Semicolon found in generated prose"))
        if is_prose and "—" in prose and profile.get("punctuation.em_dash") == "replace_with_hyphen":
            findings.append(Finding("warning", "em-dash", number, "Em dash found where the profile prefers a hyphen"))

        for pattern in (IMAGE_MD_RE, IMAGE_WIKI_RE):
            for match in pattern.finditer(normalized):
                target = clean_target(match.group(1))
                if not target or is_external(target):
                    continue
                candidate = (path.parent / target).resolve()
                if not candidate.exists():
                    findings.append(Finding("error", "missing-image", number, f"Local image does not exist: {target}"))

    if in_fence:
        findings.append(Finding("error", "unclosed-fence", len(lines), "Code fence is not closed"))

    math_spans, unclosed_math = find_math_spans(content_lines)
    for line, content in math_spans:
        if NON_ENGLISH_SCRIPT_RE.search(content):
            findings.append(
                Finding(
                    "error",
                    "non-english-text-in-latex",
                    line,
                    "Non-English linguistic script found inside LaTeX math",
                )
            )
    if unclosed_math == "$$":
        findings.append(Finding("error", "unclosed-display-math", len(lines), "Display math block is not closed"))

    previous_level = 0
    for line_no, level, _title in headings:
        if previous_level and level > previous_level + 1:
            findings.append(
                Finding("warning", "heading-jump", line_no, f"Heading jumps from H{previous_level} to H{level}")
            )
        previous_level = level

    check_tables(content_lines, findings)
    check_learning_sections(headings, profile, findings)
    return sorted(findings, key=lambda item: (item.line, item.level, item.code))


def split_table_row(line: str) -> list[str]:
    stripped = line.strip().strip("|")
    return re.split(r"(?<!\\)\|", stripped)


def check_tables(lines: list[str | None], findings: list[Finding]) -> None:
    index = 0
    separator = re.compile(r"\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*")
    while index < len(lines) - 1:
        header, divider = lines[index], lines[index + 1]
        if header is None or divider is None or "|" not in header or not separator.fullmatch(divider):
            index += 1
            continue
        expected = len(split_table_row(header))
        cursor = index + 2
        while cursor < len(lines) and lines[cursor] is not None and "|" in lines[cursor] and lines[cursor].strip():
            actual = len(split_table_row(lines[cursor]))
            if actual != expected:
                findings.append(
                    Finding(
                        "error",
                        "table-width",
                        cursor + 1,
                        f"Table row has {actual} cells, expected {expected}",
                    )
                )
            cursor += 1
        index = cursor


def check_learning_sections(
    headings: list[tuple[int, int, str]], profile: dict[str, object], findings: list[Finding]
) -> None:
    titles = [title.casefold() for _, _, title in headings]
    language = str(profile.get("output_language", "English"))
    requested = ("glossary", "one_sentence_takeaway", "common_mistakes")
    for key in requested:
        if not _enabled(profile.get(key)):
            continue
        aliases = profile.get(f"section_headings.{language}.{key}")
        if isinstance(aliases, str):
            aliases = [aliases]
        if not isinstance(aliases, list) or not aliases:
            findings.append(
                Finding(
                    "info",
                    f"unverifiable-{key.replace('_', '-')}",
                    1,
                    f"No configured {language} heading aliases; cannot verify the requested section",
                )
            )
            continue
        normalized_aliases = [str(alias).casefold() for alias in aliases]
        if not any(any(alias in title for alias in normalized_aliases) for title in titles):
            findings.append(
                Finding(
                    "warning",
                    f"missing-{key.replace('_', '-')}",
                    1,
                    f"Effective profile requests a {key.replace('_', ' ')} section",
                )
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("note", type=Path)
    parser.add_argument("--profile", type=Path, help="Selected profile overlaid on bundled defaults")
    parser.add_argument(
        "--set",
        action="append",
        default=[],
        dest="overrides",
        metavar="KEY=VALUE",
        help="Request-specific dotted-key override; repeat as needed",
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--strict", action="store_true", help="Return nonzero for warnings as well as errors")
    args = parser.parse_args(argv)

    if not args.note.is_file():
        parser.error(f"note does not exist: {args.note}")
    if args.profile and not args.profile.is_file():
        parser.error(f"profile does not exist: {args.profile}")
    try:
        profile = load_effective_profile(args.profile, args.overrides)
    except ValueError as error:
        parser.error(str(error))

    findings = check_note(args.note, profile)
    if args.as_json:
        print(json.dumps([asdict(item) for item in findings], ensure_ascii=False, indent=2))
    elif findings:
        for item in findings:
            print(f"{item.level.upper():7} {item.code:32} line {item.line}: {item.message}")
    else:
        print("OK: no structural or configured-style issues found")

    has_errors = any(item.level == "error" for item in findings)
    return 1 if has_errors or (args.strict and any(item.level == "warning" for item in findings)) else 0


if __name__ == "__main__":
    sys.exit(main())
