from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.omr import convert_with_audiveris, validate_input

ROOT = Path(__file__).resolve().parents[1]
UPLOAD_DIR = ROOT / "storage" / "uploads"
OUTPUT_DIR = ROOT / "storage" / "outputs"
STATIC_DIR = ROOT / "static"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Partitura Converter", version="0.1.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, object]:
    return {
        "ok": True,
        "audiveris_available": shutil.which("audiveris") is not None,
        "formats": ["pdf", "jpg", "jpeg", "png"],
        "exports": ["musicxml", "mxl"],
    }


@app.post("/api/convert")
async def convert(file: UploadFile = File(...)) -> dict[str, object]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Arquivo sem nome.")
    try:
        validate_input(file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    safe_name = Path(file.filename).name
    input_path = UPLOAD_DIR / safe_name
    with input_path.open("wb") as handle:
        while chunk := await file.read(1024 * 1024):
            handle.write(chunk)

    result = convert_with_audiveris(input_path, OUTPUT_DIR)
    return {
        "job_id": result.job_id,
        "status": result.status,
        "message": result.message,
        "outputs": [f"/api/download/{path}" for path in result.output_files],
        "log": result.log[-4000:],
    }


@app.get("/api/download/{job_id}/{filename}")
def download(job_id: str, filename: str) -> FileResponse:
    path = OUTPUT_DIR / job_id / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")
    return FileResponse(path, filename=filename)
