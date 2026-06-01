from __future__ import annotations

import json
from pathlib import Path

import pytest

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"


def assert_matches_snapshot(name: str, actual: str) -> None:
    snapshot_path = SNAPSHOT_DIR / name
    if not snapshot_path.exists():
        pytest.fail(f"Snapshot missing: {snapshot_path}")
    expected = snapshot_path.read_text()
    assert actual == expected


def stable_json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
