import os
import tempfile
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from models.schemas import Lead
from services.job_store import get_job
from services.excel_service import save_excel
from services.sheets_service import push_to_sheets

router = APIRouter()


class ExportRequest(BaseModel):
    job_id: str
    spreadsheet_url: Optional[str] = None


@router.get("/download-excel/{job_id}")
def download_excel(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not job.leads:
        raise HTTPException(status_code=400, detail="No leads available")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    tmp.close()
    save_excel(job.leads, tmp.name)

    # Generate filename from search query if possible
    safe_filename = "extracted_leads.xlsx"
    if job.maps_url:
        import re
        from urllib.parse import unquote
        match = re.search(r"search/([^/@?]+)", job.maps_url)
        if match:
            query = unquote(match.group(1)).replace("+", "_").strip()
            if query:
                safe_filename = f"{query}_leads.xlsx"

    return FileResponse(
        tmp.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=safe_filename,
        headers={
            "Content-Disposition": f'attachment; filename="{safe_filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )


@router.post("/push-to-sheets")
def push_sheets(req: ExportRequest):
    job = get_job(req.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not job.leads:
        raise HTTPException(status_code=400, detail="No leads available")
    if not req.spreadsheet_url:
        raise HTTPException(status_code=400, detail="spreadsheet_url is required")

    result = push_to_sheets(job.leads, req.spreadsheet_url)
    return result
