#!/usr/bin/env python3
"""Install the canonical Obsidian Summarizer skill for a supported host."""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


SKILL_NAME = "obsidian-summarizer"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_SOURCE = REPOSITORY_ROOT / "skills" / SKILL_NAME
PLATFORM_DIRS = {
    "codex": {"user": (".agents", "skills"), "project": (".agents", "skills")},
    "claude-code": {"user": (".claude", "skills"), "project": (".claude", "skills")},
    "gemini-cli": {"user": (".gemini", "skills"), "project": (".gemini", "skills")},
    "antigravity": {
        "user": (".gemini", "config", "skills"),
        "project": (".agents", "skills"),
    },
    "cursor": {"user": (".cursor", "skills"), "project": (".cursor", "skills")},
}


class InstallError(RuntimeError):
    """An actionable installation failure with a stable process exit code."""

    def __init__(self, message: str, exit_code: int = 4) -> None:
        super().__init__(message)
        self.exit_code = exit_code


@dataclass(frozen=True)
class InstallResult:
    """Describe the paths and action produced by an installation attempt."""

    source: Path
    target: Path
    action: str
    backup: Path | None = None


def resolve_target(
    platform: str,
    scope: str,
    project_dir: Path | None = None,
    home_dir: Path | None = None,
) -> Path:
    """Return the documented installation target for a host and scope."""
    if platform not in PLATFORM_DIRS:
        raise InstallError(f"unsupported platform: {platform}", 2)
    if scope not in {"user", "project"}:
        raise InstallError(f"unsupported scope: {scope}", 2)
    if scope == "project":
        if project_dir is None:
            raise InstallError("--project-dir is required for project scope", 2)
        base = project_dir.expanduser().resolve()
    else:
        if project_dir is not None:
            raise InstallError("--project-dir is only valid for project scope", 2)
        base = (home_dir or Path.home()).expanduser().resolve()
    return base.joinpath(*PLATFORM_DIRS[platform][scope], SKILL_NAME)


def _validate_source(source: Path) -> Path:
    source = source.resolve()
    if source.name != SKILL_NAME or not (source / "SKILL.md").is_file():
        raise InstallError(f"canonical skill source is invalid: {source}")
    symlinks = [path for path in source.rglob("*") if path.is_symlink()]
    if symlinks:
        raise InstallError(f"canonical skill contains a symlink and will not be copied: {symlinks[0]}")
    return source


def _trees_equal(left: Path, right: Path) -> bool:
    if not left.is_dir() or not right.is_dir():
        return False
    comparison = filecmp.dircmp(left, right)
    if comparison.left_only or comparison.right_only or comparison.funny_files:
        return False
    if any(not filecmp.cmp(left / name, right / name, shallow=False) for name in comparison.common_files):
        return False
    return all(_trees_equal(left / name, right / name) for name in comparison.common_dirs)


def _backup_path(target: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    candidate = target.with_name(f"{target.name}.backup-{stamp}")
    counter = 1
    while candidate.exists() or candidate.is_symlink():
        candidate = target.with_name(f"{target.name}.backup-{stamp}-{counter}")
        counter += 1
    return candidate


def _symlink_component(path: Path) -> Path | None:
    for candidate in (path, *path.parents):
        if candidate.is_symlink():
            return candidate
    return None


def install_skill(source: Path, target: Path, *, dry_run: bool = False, update: bool = False) -> InstallResult:
    """Copy one canonical skill safely, backing up an existing target on update."""
    source = _validate_source(source)
    target = target.expanduser().absolute()
    if target == source or target in source.parents or source in target.parents:
        raise InstallError("source and target must be separate directories")
    symlink_component = _symlink_component(target)
    if symlink_component is not None:
        raise InstallError(f"refusing target with symlink path component: {symlink_component}", 3)

    exists = target.exists()
    if exists and not target.is_dir():
        raise InstallError(f"target exists and is not a directory: {target}", 3)
    if exists:
        target_symlinks = [path for path in target.rglob("*") if path.is_symlink()]
        if target_symlinks:
            raise InstallError(
                f"existing target contains a symlink and will not be inspected or replaced: "
                f"{target_symlinks[0]}",
                3,
            )
    if exists and not update:
        raise InstallError(f"target already exists; rerun with --update to back it up first: {target}", 3)
    if exists and update and _trees_equal(source, target):
        return InstallResult(source, target, "already-current")

    backup = _backup_path(target) if exists else None
    if dry_run:
        return InstallResult(source, target, "would-update" if exists else "would-install", backup)

    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix=f".{SKILL_NAME}-", dir=target.parent) as temp_dir:
            staged = Path(temp_dir) / SKILL_NAME
            shutil.copytree(source, staged)
            if backup is not None:
                target.rename(backup)
            try:
                staged.rename(target)
            except OSError:
                if backup is not None and backup.exists() and not target.exists():
                    backup.rename(target)
                raise
    except OSError as error:
        raise InstallError(f"installation failed for {target}: {error}") from error
    return InstallResult(source, target, "updated" if exists else "installed", backup)


def build_parser() -> argparse.ArgumentParser:
    """Build the installer command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", required=True, choices=sorted(PLATFORM_DIRS))
    parser.add_argument("--scope", required=True, choices=("user", "project"))
    parser.add_argument("--project-dir", type=Path, help="Project root; required for project scope")
    parser.add_argument("--dry-run", action="store_true", help="Show resolved paths without writing")
    parser.add_argument(
        "--update",
        action="store_true",
        help="Replace an existing target only after moving it to a timestamped backup",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the installer CLI and return a documented exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        target = resolve_target(args.platform, args.scope, args.project_dir)
        print(f"Source: {CANONICAL_SOURCE.resolve()}")
        print(f"Target: {target}")
        result = install_skill(CANONICAL_SOURCE, target, dry_run=args.dry_run, update=args.update)
    except InstallError as error:
        print(f"Error: {error}", file=sys.stderr)
        return error.exit_code

    print(f"Action: {result.action}")
    if result.backup is not None:
        print(f"Backup: {result.backup}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
