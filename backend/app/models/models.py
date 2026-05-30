from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(Text, nullable=False)
    page_type = Column(String(50))
    status = Column(String(20), default="pending")
    scraped_at = Column(DateTime, default=func.now())
    row_count = Column(Integer, default=0)

    # Cascade: deleting a job also deletes its scraped data
    scraped_data = relationship("ScrapedData", back_populates="job", cascade="all, delete-orphan")


class ScrapedData(Base):
    __tablename__ = "scraped_data"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("scrape_jobs.id", ondelete="CASCADE"), nullable=False)
    data = Column(JSON)
    cleaned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    job = relationship("ScrapeJob", back_populates="scraped_data")