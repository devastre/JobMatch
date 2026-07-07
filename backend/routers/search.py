import uuid
import asyncio
from typing import Optional, Dict, Any
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import SessionLocal, get_db
from models import CV, Match
from schemas import SearchRequest

router = APIRouter()

search_jobs: Dict[str, Dict[str, Any]] = {}

async def process_search(search_id: str, cv_id: int):
    await asyncio.sleep(2)
    
    db = SessionLocal()
    try:
        matches = db.query(Match).filter(Match.cv_id == cv_id).all()
        
        results = []
        for match in matches:
            job = match.job_offer
            results.append({
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "score": match.score
            })
        
        results.sort(key=lambda x: x["score"], reverse=True)
        
        search_jobs[search_id]["status"] = "completed"
        search_jobs[search_id]["results"] = results
    except Exception as e:
        search_jobs[search_id]["status"] = "failed"
        search_jobs[search_id]["error"] = str(e)
    finally:
        db.close()

@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def create_search(request: SearchRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    cv = db.query(CV).filter(CV.id == request.cv_id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
        
    search_id = str(uuid.uuid4())
    search_jobs[search_id] = {"status": "pending", "results": None}
    
    background_tasks.add_task(process_search, search_id, request.cv_id)
    
    return {"search_id": search_id}

@router.get("/{search_id}/results")
async def get_search_results(search_id: str, location: Optional[str] = None):
    if search_id not in search_jobs:
        raise HTTPException(status_code=404, detail="Search job not found")
        
    job = search_jobs[search_id]
    if job["status"] == "pending":
        return {"status": "pending"}
        
    if job["status"] == "failed":
        raise HTTPException(status_code=500, detail="Search job failed")
        
    results = job["results"]
    
    if location:
        results = [r for r in results if r["location"] and location.lower() in r["location"].lower()]
        
    return {"status": "completed", "results": results}
