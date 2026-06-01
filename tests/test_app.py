from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.omr import validate_input

client = TestClient(app)


def test_health_reports_supported_formats():
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.json()
    assert data['ok'] is True
    assert 'pdf' in data['formats']
    assert 'musicxml' in data['exports']


def test_validate_input_accepts_pdf_and_images():
    assert validate_input('score.pdf') == '.pdf'
    assert validate_input('score.JPG') == '.jpg'
    assert validate_input('score.png') == '.png'


def test_validate_input_rejects_unknown_extension():
    try:
        validate_input('score.txt')
    except ValueError as exc:
        assert 'Formato não suportado' in str(exc)
    else:
        raise AssertionError('validate_input should reject .txt')


def test_convert_rejects_unsupported_upload():
    response = client.post(
        '/api/convert',
        files={'file': ('score.txt', b'not a score', 'text/plain')},
    )
    assert response.status_code == 400
    assert 'Formato não suportado' in response.json()['detail']
