from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.omr import build_audiveris_command, target_profiles, validate_input

client = TestClient(app)


def test_health_reports_supported_formats():
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.json()
    assert data['ok'] is True
    assert 'pdf' in data['formats']
    assert 'musicxml' in data['exports']
    assert 'musescore' in data['targets']


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


def test_build_audiveris_command_uses_script_when_configured(tmp_path, monkeypatch):
    monkeypatch.setenv('AUDIVERIS_CMD', '/opt/audiveris/bin/Audiveris')
    command = build_audiveris_command(tmp_path / 'score.pdf', tmp_path / 'out')
    assert command[:4] == ['/opt/audiveris/bin/Audiveris', '-batch', '-export', '-output']


def test_target_profiles_document_supported_apps():
    profiles = target_profiles()
    assert profiles['musescore']['free'] is True
    assert profiles['guitar_pro']['input'] == 'MusicXML'
    assert profiles['encore']['input'] == 'MusicXML/MIDI'


def test_convert_batch_accepts_multiple_files_when_omr_missing():
    response = client.post(
        '/api/convert/batch',
        files=[
            ('files', ('piano.pdf', b'%PDF-1.4', 'application/pdf')),
            ('files', ('guitar.png', b'not really png', 'image/png')),
        ],
    )
    assert response.status_code == 200
    data = response.json()
    assert data['count'] == 2
    assert [item['filename'] for item in data['results']] == ['piano.pdf', 'guitar.png']
