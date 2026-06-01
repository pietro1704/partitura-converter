from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.omr import audiveris_available, convert_with_audiveris, target_profiles, validate_input

ROOT = Path(__file__).resolve().parents[1]
UPLOAD_DIR = ROOT / "storage" / "uploads"
OUTPUT_DIR = ROOT / "storage" / "outputs"
STATIC_DIR = ROOT / "static"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Partitura Converter", version="0.2.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, object]:
    return {
        "ok": True,
        "audiveris_available": audiveris_available(),
        "formats": ["pdf", "jpg", "jpeg", "png"],
        "exports": ["musicxml", "mxl"],
        "targets": target_profiles(),
    }


async def save_upload(file: UploadFile) -> Path:
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
    return input_path


def serialize_result(filename: str, result) -> dict[str, object]:
    return {
        "filename": filename,
        "job_id": result.job_id,
        "status": result.status,
        "message": result.message,
        "outputs": [f"/api/download/{path}" for path in result.output_files],
        "log": result.log[-4000:],
    }


@app.post("/api/convert")
async def convert(file: UploadFile = File(...)) -> dict[str, object]:
    input_path = await save_upload(file)
    result = convert_with_audiveris(input_path, OUTPUT_DIR)
    return serialize_result(Path(file.filename or input_path.name).name, result)


@app.post("/api/convert/batch")
async def convert_batch(files: list[UploadFile] = File(...)) -> dict[str, object]:
    results = []
    for file in files:
        input_path = await save_upload(file)
        result = convert_with_audiveris(input_path, OUTPUT_DIR)
        results.append(serialize_result(Path(file.filename or input_path.name).name, result))
    return {"count": len(results), "results": results}


@app.get("/api/download/{job_id}/{filename}")
def download(job_id: str, filename: str) -> FileResponse:
    path = OUTPUT_DIR / job_id / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")
    return FileResponse(path, filename=filename)
