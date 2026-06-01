from __future__ import annotations

from app.main import serialize_result
from app.omr import ConversionResult, audiveris_available, convert_with_audiveris


def test_audiveris_available_accepts_absolute_executable(tmp_path, monkeypatch):
    executable = tmp_path / 'audiveris'
    executable.write_text('#!/bin/sh\n')
    monkeypatch.setenv('AUDIVERIS_CMD', str(executable))

    assert audiveris_available() is True


def test_convert_with_audiveris_reports_configured_missing_command(tmp_path, monkeypatch):
    monkeypatch.setenv('AUDIVERIS_CMD', '/missing/audiveris')
    input_path = tmp_path / 'score.pdf'
    input_path.write_bytes(b'%PDF-1.4')

    result = convert_with_audiveris(input_path, tmp_path / 'out')

    assert result.status == 'missing_omr'
    assert result.output_files == []
    assert result.log == 'command not found: /missing/audiveris'


def test_serialize_result_truncates_large_logs():
    result = ConversionResult(
        job_id='abc123',
        status='failed',
        message='Falhou.',
        output_files=['abc123/score.mxl'],
        log='x' * 5000,
    )

    payload = serialize_result('score.pdf', result)

    assert payload['outputs'] == ['/api/download/abc123/score.mxl']
    assert len(payload['log']) == 4000
    assert payload['log'] == 'x' * 4000
