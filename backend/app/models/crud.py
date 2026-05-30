from sqlalchemy.orm import Session
from app.models.models import ScrapeJob, ScrapedData
from datetime import datetime

def create_scrape_job(db: Session, url: str, page_type: str) -> ScrapeJob:
    """Create a new scrape job record with status 'processing'."""
    job = ScrapeJob(
        url=url,
        page_type=page_type,
        status="processing",
        scraped_at=datetime.now(),
        row_count=0
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def update_job_status(db: Session, job_id: int, status: str, row_count: int = 0) -> ScrapeJob:
    """Update a job's status and row count after scraping completes."""
    job = db.query(ScrapeJob).filter(ScrapeJob.id == job_id).first()
    if job:
        job.status = status
        job.row_count = row_count
        db.commit()
        db.refresh(job)
    return job


def save_scraped_data(db: Session, job_id: int, data: dict) -> ScrapedData:
    """Save cleaned scraped data linked to a job."""
    record = ScrapedData(
        job_id=job_id,
        data=data,
        cleaned=True,
        created_at=datetime.now()
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_all_jobs(db: Session, skip: int = 0, limit: int = 100) -> list:
    """Get scrape jobs with pagination, ordered by most recent."""
    return (
        db.query(ScrapeJob)
        .order_by(ScrapeJob.scraped_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_job_count(db: Session) -> int:
    """Get total number of scrape jobs."""
    return db.query(ScrapeJob).count()


def get_job_by_id(db: Session, job_id: int) -> ScrapeJob:
    """Get a single scrape job by ID."""
    return db.query(ScrapeJob).filter(ScrapeJob.id == job_id).first()


def get_data_by_job_id(db: Session, job_id: int) -> ScrapedData:
    """Get scraped data for a specific job."""
    return db.query(ScrapedData).filter(ScrapedData.job_id == job_id).first()


def delete_job(db: Session, job_id: int) -> bool:
    """Delete a job and its data."""
    job = db.query(ScrapeJob).filter(ScrapeJob.id == job_id).first()
    if not job:
        return False
    data = db.query(ScrapedData).filter(ScrapedData.job_id == job_id).all()
    for d in data:
        db.delete(d)
    db.delete(job)
    db.commit()
    return True