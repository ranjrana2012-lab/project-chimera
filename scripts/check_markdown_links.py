#!/usr/bin/env python3
"""Check local markdown links without external network dependencies."""

import argparse
import re
import sys
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


INLINE_MARKDOWN_LINK = re.compile(
    r"(?<!!)\[[^\]\n]+\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)"
)
EXTERNAL_PREFIXES = (
    "http://",
    "https://",
    "mailto:",
    "tel:",
    "ftp://",
)


@dataclass(frozen=True)
class BrokenLink:
    source: Path
    target: str
    resolved: Path


def iter_markdown_files(paths: Sequence[Path], repo_root: Path) -> Iterable[Path]:
    for path in paths:
        absolute = path if path.is_absolute() else repo_root / path
        if absolute.is_dir():
            yield from sorted(absolute.rglob("*.md"))
        elif absolute.is_file() and absolute.suffix.lower() == ".md":
            yield absolute


def normalize_target(target: str) -> str:
    return target.strip().strip("<>")


def is_external_target(target: str) -> bool:
    return target.lower().startswith(EXTERNAL_PREFIXES)


def target_path_part(target: str) -> str:
    return target.split("#", 1)[0].split("?", 1)[0]


def resolve_local_target(source: Path, target: str, repo_root: Path) -> Path:
    path_part = urllib.parse.unquote(target_path_part(target))
    if path_part.startswith("/"):
        return repo_root / path_part.lstrip("/")

    source_relative = source.parent / path_part
    repo_relative = repo_root / path_part
    if not source_relative.exists() and repo_relative.exists():
        return repo_relative
    return source_relative


def find_broken_links(paths: Sequence[Path], repo_root: Path) -> list[BrokenLink]:
    broken: list[BrokenLink] = []
    repo_root = repo_root.resolve()

    for markdown_file in iter_markdown_files(paths, repo_root):
        content = markdown_file.read_text(encoding="utf-8")
        for match in INLINE_MARKDOWN_LINK.finditer(content):
            target = normalize_target(match.group(1))
            if not target or is_external_target(target):
                continue

            path_part = target_path_part(target)
            if not path_part:
                continue

            resolved = resolve_local_target(markdown_file, target, repo_root)
            if not resolved.exists():
                broken.append(BrokenLink(markdown_file, target, resolved))

    return broken


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path("docs"), Path("README.md")],
        help="Markdown files or directories to scan.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root used for repo-relative markdown links.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    repo_root = args.repo_root.resolve()
    broken = find_broken_links(args.paths, repo_root=repo_root)

    if broken:
        for item in broken:
            source = item.source.relative_to(repo_root)
            print(f"BROKEN: {source}: {item.target} -> {item.resolved}")
        print(f"Found {len(broken)} broken markdown link(s).")
        return 1

    print("No broken markdown links found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
