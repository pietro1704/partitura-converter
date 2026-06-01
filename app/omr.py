from __future__ import annotations

import shutil
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path


ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


@dataclass(frozen=True)
class ConversionResult:
    job_id: str
    status: str
    message: str
    output_files: list[str]
    log: str


def audiveris_available() -> bool:
    return shutil.which("audiveris") is not None


def validate_input(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise ValueError(f"Formato não suportado: {suffix or 'sem extensão'}. Use {allowed}.")
    return suffix


def convert_with_audiveris(input_path: Path, output_root: Path, timeout_seconds: int = 300) -> ConversionResult:
    validate_input(input_path.name)
    job_id = uuid.uuid4().hex[:12]
    job_output = output_root / job_id
    job_output.mkdir(parents=True, exist_ok=True)

    if not audiveris_available():
        return ConversionResult(
            job_id=job_id,
            status="missing_omr",
            message="Audiveris não está instalado ou não está no PATH. Instale Audiveris para conversão real.",
            output_files=[],
            log="command not found: audiveris",
        )

    command = [
        "audiveris",
        "-batch",
        "-export",
        "-output",
        str(job_output),
        str(input_path),
    ]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
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
