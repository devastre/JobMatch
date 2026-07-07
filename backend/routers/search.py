import uuid
import asyncio
import urllib.request
import urllib.error
import json
from typing import Optional, Dict, Any
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import SessionLocal, get_db
from models import CV, Match
from schemas import SearchRequest
from matching import calculate_match_score

router = APIRouter()

search_jobs: Dict[str, Dict[str, Any]] = {}

async def process_search(search_id: str, cv_id: int):
    db = SessionLocal()
    try:
        cv = db.query(CV).filter(CV.id == cv_id).first()
        if not cv:
            raise Exception("CV not found")
            
        url = "https://www.themuse.com/api/public/jobs?page=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
        except urllib.error.URLError as e:
            raise Exception(f"External API failed or timed out: {str(e)}")
            
        jobs_data = data.get("results", [])
        
        results = []
        cv_text = cv.parsed_json.get("raw_text", "") if cv.parsed_json else ""
        cv_skills = cv.parsed_json.get("skills", []) if cv.parsed_json else []
        
        for job in jobs_data:
            job_desc = job.get("contents", "")
            job_title = job.get("name", "")
            company = job.get("company", {}).get("name", "")
            locations = job.get("locations", [])
            location = locations[0].get("name", "") if locations else "Remote"
            job_url = job.get("refs", {}).get("landing_page", "")
            
            match_info = calculate_match_score(cv_text, job_desc, cv_skills)
            
            results.append({
                "id": str(job.get("id")),
                "title": job_title,
                "company": company,
                "location": location,
                "url": job_url,
                "score": match_info["score"],
                "keywords": match_info["matched_keywords"]
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
        error_msg = job.get("error", "Search job failed")
        raise HTTPException(status_code=500, detail=error_msg)
        
    results = job["results"]
    
    if location:
        results = [r for r in results if r["location"] and location.lower() in r["location"].lower()]
        
    return {"status": "completed", "results": results}
