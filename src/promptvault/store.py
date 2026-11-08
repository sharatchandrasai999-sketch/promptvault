"""On-disk storage for prompt versions.

Each prompt lives in one JSON file inside the store directory::

    <store>/<name>.json
        {"name": ..., "versions": [{"version": 1, "text": ..., "created": ...}, ...]}

The store directory defaults to ``~/.promptvault`` and can be overridden
with the ``PROMPTVAULT_STORE`` environment variable or ``--store``.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

ENV_VAR = "PROMPTVAULT_STORE"
DEFAULT_STORE = Path.home() / ".promptvault"


class PromptVaultError(Exception):
    """A user-facing error (missing prompt, missing version, bad input)."""


def resolve_store(explicit: str | None = None) -> Path:
    """Pick the store directory: explicit flag, then env var, then default."""
    if explicit:
        return Path(explicit).expanduser()
    env = os.environ.get(ENV_VAR)
    if env:
        return Path(env).expanduser()
    return DEFAULT_STORE


def _safe_name(name: str) -> str:
    if not name or not name.strip():
        raise PromptVaultError("prompt name must not be empty")
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", name.strip())
    if safe in {".", ".."}:
        raise PromptVaultError(f"invalid prompt name: {name!r}")
    return safe


def _prompt_file(store: Path, name: str) -> Path:
    return store / f"{_safe_name(name)}.json"


def _read(store: Path, name: str) -> dict:
    path = _prompt_file(store, name)
    if not path.exists():
        raise PromptVaultError(f"no prompt named {name!r} in {store}")
    return json.loads(path.read_text(encoding="utf-8"))


def save_prompt(store: Path, name: str, text: str) -> int:
    """Append a new version of ``name`` and return its version number."""
    if not text or not text.strip():
        raise PromptVaultError("prompt text must not be empty")
    store.mkdir(parents=True, exist_ok=True)
    path = _prompt_file(store, name)
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = {"name": name, "versions": []}
    version = len(data["versions"]) + 1
    data["versions"].append(
        {
            "version": version,
            "text": text,
            "created": datetime.now(timezone.utc).isoformat(),
        }
    )
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return version


def list_prompts(store: Path) -> list[tuple[str, int]]:
    """Return ``(name, version_count)`` for every saved prompt, sorted by name."""
    if not store.exists():
        return []
    result = []
    for path in sorted(store.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        result.append((data.get("name", path.stem), len(data.get("versions", []))))
    return result


def list_versions(store: Path, name: str) -> list[dict]:
    """Return all versions of ``name``, oldest first."""
    return _read(store, name)["versions"]


def get_version(store: Path, name: str, version: int) -> dict:
    """Return one version dict, or raise a clean error if it is missing."""
    for entry in _read(store, name)["versions"]:
        if entry["version"] == version:
            return entry
    raise PromptVaultError(f"prompt {name!r} has no version {version}")
