"""Import compatibility for the hyphenated Kimi service directory."""

from pathlib import Path

_legacy_dir = Path(__file__).resolve().parent.parent / "kimi-super-agent"

if _legacy_dir.exists():
    __path__ = [str(_legacy_dir)] + list(__path__)
