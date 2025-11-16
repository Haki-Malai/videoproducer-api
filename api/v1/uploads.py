from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, UploadFile, status

from app.tasks.uploads import process_uploaded_file

uploads_router = APIRouter(prefix="/uploads", tags=["Uploads"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@uploads_router.post(
    "/files",
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_file(file: UploadFile = File(...)) -> dict[str, str]:
    """Accept a file upload and process it asynchronously with Celery."""
    suffix = Path(file.filename).suffix
    dest = UPLOAD_DIR / f"{uuid4().hex}{suffix}"

    with dest.open("wb") as out_file:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            out_file.write(chunk)

    process_uploaded_file.delay(str(dest))
    return {"path": str(dest)}
