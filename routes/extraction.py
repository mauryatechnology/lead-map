import asyncio
import threading
import uuid
from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, HTTPException
from models.schemas import ExtractionRequest, ExtractionStatus, StopRequest
from services.job_store import create_job, get_job, update_job, list_jobs
from scraper.maps_scraper import extract_leads, request_stop

router = APIRouter()


def _run_extraction(job_id: str, req: ExtractionRequest):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(
            extract_leads(
                job_id=job_id,
                maps_url=req.maps_url,
                city=req.city,
                scroll_delay=req.scroll_delay,
                max_results=req.max_results,
            )
        )
    finally:
        loop.close()


@router.post("/start-extraction", response_model=ExtractionStatus)
def start_extraction(req: ExtractionRequest):
    job_id = str(uuid.uuid4())
    status = ExtractionStatus(
        job_id=job_id,
        status="pending",
        started_at=datetime.now().isoformat(),
        progress_message="Queued...",
        maps_url=req.maps_url,
    )
    create_job(job_id, status)

    t = threading.Thread(target=_run_extraction, args=(job_id, req), daemon=True)
    t.start()

    return status


@router.get("/status/{job_id}", response_model=ExtractionStatus)
def get_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/stop-extraction")
def stop_extraction(req: StopRequest):
    job = get_job(req.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    request_stop(req.job_id)
    update_job(req.job_id, progress_message="Stop requested...")
    return {"message": "Stop signal sent", "job_id": req.job_id}


@router.get("/jobs")
def get_all_jobs():
    jobs = list_jobs()
    return [
        {
            "job_id": j.job_id,
            "status": j.status,
            "total_found": j.total_found,
            "started_at": j.started_at,
        }
        for j in jobs
    ]
@router.post("/update-lead-note/{job_id}/{index}")
def update_lead_note(job_id: str, index: int, req: dict):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if index < 0 or index >= len(job.leads):
        raise HTTPException(status_code=400, detail="Invalid lead index")
    
    note = req.get("note", "")
    job.leads[index].notes = note
    return {"message": "Note updated", "job_id": job_id, "index": index}
