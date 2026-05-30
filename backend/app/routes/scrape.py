from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.scrapers.scraper import run_scraper
from app.scrapers.amazon_extractor import extract_amazon_products
from app.scrapers.flipkart_extractor import extract_flipkart_products
from app.scrapers.product_extractor import extract_products
from app.scrapers.jsonld_extractor import extract_jsonld
from app.scrapers.linkedin_extractor import extract_linkedin_jobs
from app.scrapers.job_extractor import extract_jobs_remotive
from app.analyzers.job_analyzer import analyze_jobs
from app.models.crud import (
    create_scrape_job, save_scraped_data, update_job_status,
    get_all_jobs, get_job_count, get_job_by_id,
    get_data_by_job_id, delete_job
)
from app.exporters.exporter import to_csv, to_excel, to_json
import io

router = APIRouter(prefix="/api", tags=["scraper"])

class ScrapeRequest(BaseModel):
    url: str
    force_playwright: bool = False


@router.post("/scrape")
def scrape(request: ScrapeRequest, db: Session = Depends(get_db)):
    """Scrape a URL, clean data, save to MySQL."""
    try:
        result = run_scraper(request.url, request.force_playwright)

        cleaned = result["cleaned_data"]
        page_type = result["page_type"]

        # Amazon: run specialized extractor on top of scraped HTML
        if page_type == "amazon_products":
            raw_html = result.get("raw_html", "")
            amazon_data = extract_amazon_products(raw_html, request.url)
            cleaned = amazon_data
            row_count = amazon_data.get("total", 0)
        elif page_type == "flipkart_products":
            raw_html = result.get("raw_html", "")
            flipkart_data = extract_flipkart_products(raw_html, request.url)
            cleaned = flipkart_data
            row_count = flipkart_data.get("total", 0)
        elif page_type == "products":
            raw_html = result.get("raw_html", "")
            product_data = extract_products(raw_html, request.url)
            cleaned = product_data
            row_count = product_data.get("total", 0)
        elif page_type == "jsonld":
            raw_html = result.get("raw_html", "")
            jsonld_data = extract_jsonld(raw_html, request.url)
            cleaned = jsonld_data
            row_count = jsonld_data.get("total", 0)
        elif page_type == "linkedin_jobs":
            raw_html = result.get("raw_html", "")
            linkedin_data = extract_linkedin_jobs(raw_html, request.url)
            cleaned = linkedin_data
            row_count = linkedin_data.get("total", 0)
        elif page_type == "table":
            tables = cleaned.get("tables", [])
            row_count = 0
            if tables:
                best = max(tables, key=lambda t: len(t.get("rows", [])))
                row_count = best.get("stats", {}).get("cleaned_rows", 0)
        elif page_type == "article":
            paragraphs = cleaned.get("data", {}).get("paragraphs", [])
            row_count = len(paragraphs)
        elif page_type == "json":
            row_count = len(cleaned.get("data", {}).get("data", []))
        else:
            row_count = 0

        job = create_scrape_job(db, request.url, page_type)
        save_scraped_data(db, job.id, cleaned)
        update_job_status(db, job.id, "completed", row_count)

        return {
            "job_id": job.id,
            "url": request.url,
            "page_type": page_type,
            "method": result["method"],
            "row_count": row_count,
            "cleaned_data": cleaned
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/market")
def job_market(category: str = "software-dev", limit: int = 100, db: Session = Depends(get_db)):
    """Fetch and analyze job market data from Remotive."""
    try:
        result = extract_jobs_remotive(category, limit)
        jobs = result.get("jobs", [])
        intelligence = analyze_jobs(jobs)

        job_record = create_scrape_job(
            db,
            f"remotive.com/api/remote-jobs?category={category}",
            "jobs",
        )
        save_scraped_data(db, job_record.id, {
            "page_type": "jobs",
            "jobs": jobs,
            "intelligence": intelligence
        })
        update_job_status(db, job_record.id, "completed", len(jobs))

        return {
            "job_id": job_record.id,
            "source": "remotive",
            "category": category,
            "total_jobs": len(jobs),
            "intelligence": intelligence,
            "jobs": jobs
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/market/analyze/{job_id}")
def analyze_saved_jobs(job_id: int, db: Session = Depends(get_db)):
    """Re-analyze previously saved job data."""
    data = get_data_by_job_id(db, job_id)
    if not data:
        raise HTTPException(status_code=404, detail="No data found")

    saved = data.data
    jobs = saved.get("jobs", [])
    intelligence = analyze_jobs(jobs)

    return {
        "job_id": job_id,
        "total_jobs": len(jobs),
        "intelligence": intelligence
    }


@router.get("/jobs/market/export/{job_id}/excel")
def export_jobs_excel(job_id: int, db: Session = Depends(get_db)):
    """Export job market data as Excel with two sheets — jobs + intelligence."""
    import pandas as pd
    import io as _io

    data = get_data_by_job_id(db, job_id)
    if not data:
        raise HTTPException(status_code=404, detail="No data found")

    saved = data.data
    jobs = saved.get("jobs", [])
    intelligence = saved.get("intelligence", {})

    output = _io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Sheet 1 — all jobs
        if jobs:
            jobs_flat = []
            for j in jobs:
                jobs_flat.append({
                    "title": j.get("title"),
                    "company": j.get("company"),
                    "category": j.get("category"),
                    "skills": ", ".join(j.get("skills", [])),
                    "job_type": j.get("job_type"),
                    "location": j.get("location"),
                    "salary": j.get("salary"),
                    "published_at": j.get("published_at"),
                    "url": j.get("url")
                })
            pd.DataFrame(jobs_flat).to_excel(writer, index=False, sheet_name="Jobs")

        # Sheet 2 — top skills
        if intelligence.get("top_skills"):
            pd.DataFrame(intelligence["top_skills"]).to_excel(writer, index=False, sheet_name="Top Skills")

        # Sheet 3 — top companies
        if intelligence.get("top_companies"):
            pd.DataFrame(intelligence["top_companies"]).to_excel(writer, index=False, sheet_name="Top Companies")

        # Sheet 4 — locations
        if intelligence.get("top_locations"):
            pd.DataFrame(intelligence["top_locations"]).to_excel(writer, index=False, sheet_name="Top Locations")

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=job_market_{job_id}.xlsx"}
    )


@router.get("/jobs")
def list_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all scrape jobs with pagination."""
    jobs = get_all_jobs(db, skip=skip, limit=limit)
    total = get_job_count(db)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "jobs": [
            {
                "id": j.id,
                "url": j.url,
                "page_type": j.page_type,
                "status": j.status,
                "row_count": j.row_count,
                "scraped_at": j.scraped_at.isoformat() if j.scraped_at else None
            }
            for j in jobs
        ]
    }


@router.get("/jobs/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get a single job with its data."""
    job = get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    data = get_data_by_job_id(db, job_id)
    return {
        "id": job.id,
        "url": job.url,
        "page_type": job.page_type,
        "status": job.status,
        "row_count": job.row_count,
        "scraped_at": job.scraped_at.isoformat() if job.scraped_at else None,
        "data": data.data if data else None
    }


@router.delete("/jobs/{job_id}")
def remove_job(job_id: int, db: Session = Depends(get_db)):
    """Delete a job and its data."""
    success = delete_job(db, job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"message": f"Job {job_id} deleted"}


@router.get("/export/{job_id}/csv")
def export_csv(job_id: int, db: Session = Depends(get_db)):
    """Export job data as CSV."""
    data = get_data_by_job_id(db, job_id)
    if not data:
        raise HTTPException(status_code=404, detail="No data found for this job")
    csv_bytes = to_csv(data.data)
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=datapulse_job_{job_id}.csv"}
    )


@router.get("/export/{job_id}/excel")
def export_excel(job_id: int, db: Session = Depends(get_db)):
    """Export job data as Excel."""
    data = get_data_by_job_id(db, job_id)
    if not data:
        raise HTTPException(status_code=404, detail="No data found for this job")
    excel_bytes = to_excel(data.data)
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=datapulse_job_{job_id}.xlsx"}
    )


@router.get("/export/{job_id}/json")
def export_json(job_id: int, db: Session = Depends(get_db)):
    """Export job data as JSON."""
    data = get_data_by_job_id(db, job_id)
    if not data:
        raise HTTPException(status_code=404, detail="No data found for this job")
    json_bytes = to_json(data.data)
    return StreamingResponse(
        io.BytesIO(json_bytes),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=datapulse_job_{job_id}.json"}
    )
