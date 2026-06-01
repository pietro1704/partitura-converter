from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.omr import target_profiles
from tests.snapshot_utils import assert_matches_snapshot, stable_json

client = TestClient(app)
ROOT = Path(__file__).resolve().parents[1]


def test_target_profiles_snapshot():
    assert_matches_snapshot('target_profiles.json', stable_json(target_profiles()))


def test_health_response_shape_snapshot():
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.json()
    data['audiveris_available'] = '<bool>'
    assert_matches_snapshot('health.json', stable_json(data))


def test_index_html_snapshot():
    assert_matches_snapshot('index.html', (ROOT / 'static' / 'index.html').read_text())
