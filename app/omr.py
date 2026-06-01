from __future__ import annotations

import os
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path

from app.gpif import convert_gp_to_musicxml


ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".gp"}


@dataclass(frozen=True)
class ConversionResult:
    job_id: str
    status: str
    message: str
    output_files: list[str]
    log: str


def audiveris_command_name() -> str:
    return os.environ.get("AUDIVERIS_CMD", "audiveris")


def audiveris_available() -> bool:
    command = audiveris_command_name()
    return Path(command).exists() if "/" in command else shutil.which(command) is not None


def build_audiveris_command(input_path: Path, output_dir: Path) -> list[str]:
    return [
        audiveris_command_name(),
        "-batch",
        "-export",
        "-output",
        str(output_dir),
        str(input_path),
    ]


def target_profiles() -> dict[str, dict[str, object]]:
    return {
        "musescore": {
            "label": "MuseScore Studio",
            "free": True,
            "input": "MusicXML",
            "notes": "Melhor editor gratuito para revisar piano e guitarra depois do OMR.",
        },
        "guitar_pro": {
            "label": "Guitar Pro",
            "free": False,
            "input": "MusicXML",
            "notes": "Importe MusicXML e revise tablatura, digitação e instrumentos.",
        },
        "encore": {
            "label": "Encore",
            "free": False,
            "input": "MusicXML/MIDI",
            "notes": "Use MusicXML quando sua versão suportar; MIDI é fallback menos fiel.",
        },
    }


def validate_input(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise ValueError(f"Formato não suportado: {suffix or 'sem extensão'}. Use {allowed}.")
    return suffix


def convert_gp_package(input_path: Path, output_root: Path) -> ConversionResult:
    validate_input(input_path.name)
    job_id = uuid.uuid4().hex[:12]
    job_output = output_root / job_id
    job_output.mkdir(parents=True, exist_ok=True)
    stem = input_path.stem
    musicxml = job_output / f"{stem}.musicxml"
    encore_dir = job_output / "encore"
    guitarpro_dir = job_output / "guitarpro"
    encore_dir.mkdir(exist_ok=True)
    guitarpro_dir.mkdir(exist_ok=True)
    try:
        converted = convert_gp_to_musicxml(input_path, musicxml)
        encore_file = encore_dir / f"{stem}.musicxml"
        guitarpro_file = guitarpro_dir / input_path.name
        shutil.copy2(musicxml, encore_file)
        shutil.copy2(input_path, guitarpro_file)
    except Exception as exc:
        return ConversionResult(job_id, "failed", "Falha ao converter Guitar Pro GPIF para MusicXML.", [], repr(exc))
    outputs = [
        str(musicxml.relative_to(output_root)),
        str(encore_file.relative_to(output_root)),
        str(guitarpro_file.relative_to(output_root)),
    ]
    return ConversionResult(
        job_id,
        "completed",
        f"GP convertido: {converted.parts} partes, {converted.measures} compassos. MusicXML pronto para MuseScore/Encore; GP original preservado para Guitar Pro.",
        outputs,
        "",
    )


def convert_with_audiveris(input_path: Path, output_root: Path, timeout_seconds: int = 300) -> ConversionResult:
    suffix = validate_input(input_path.name)
    if suffix == ".gp":
        return convert_gp_package(input_path, output_root)
    job_id = uuid.uuid4().hex[:12]
    job_output = output_root / job_id
    job_output.mkdir(parents=True, exist_ok=True)

    if not audiveris_available():
        return ConversionResult(
            job_id=job_id,
            status="missing_omr",
            message="Audiveris não está instalado ou AUDIVERIS_CMD não aponta para um executável. Instale Audiveris para conversão real.",
            output_files=[],
            log=f"command not found: {audiveris_command_name()}",
        )

    command = build_audiveris_command(input_path, job_output)
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        partial_log = "\n".join(
            part.decode(errors="replace") if isinstance(part, bytes) else part
            for part in [exc.stdout, exc.stderr]
            if part
        )
        return ConversionResult(
            job_id,
            "timed_out",
            f"Audiveris excedeu o limite de {timeout_seconds}s. Tente um PDF menor ou aumente o timeout no backend.",
            [],
            partial_log,
        )

    log = "\n".join(part for part in [completed.stdout, completed.stderr] if part)
    outputs = sorted(
        str(path.relative_to(output_root))
        for pattern in ("*.mxl", "*.musicxml", "*.xml")
        for path in job_output.rglob(pattern)
    )
    if completed.returncode != 0:
        return ConversionResult(job_id, "failed", "Audiveris falhou ao converter o arquivo.", outputs, log)
    if not outputs:
        return ConversionResult(job_id, "failed", "Audiveris terminou, mas não gerou MusicXML.", [], log)
    return ConversionResult(job_id, "completed", "Conversão concluída.", outputs, log)
