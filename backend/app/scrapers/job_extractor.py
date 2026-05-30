import requests

def extract_jobs_remotive(category: str = "software-dev", limit: int = 100) -> dict:
    """
    Fetch jobs from Remotive API and extract clean structured data.
    """
    try:
        url = f"https://remotive.com/api/remote-jobs?category={category}&limit={limit}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=15)
        data = response.json()

        raw_jobs = data.get("jobs", [])
        jobs = []

        for job in raw_jobs:
            salary_raw = job.get("salary", "") or ""
            salary_raw = salary_raw.strip()

            jobs.append({
                "id": job.get("id"),
                "title": job.get("title", "").strip(),
                "company": job.get("company_name", "").strip(),
                "category": job.get("category", "").strip(),
                "skills": job.get("tags", []),
                "job_type": job.get("job_type", "").strip(),
                "location": job.get("candidate_required_location", "").strip(),
                "salary": salary_raw,
                "published_at": job.get("publication_date", ""),
                "url": job.get("url", "")
            })

        return {
            "source": "remotive",
            "total": len(jobs),
            "jobs": jobs
        }

    except Exception as e:
        return {
            "source": "remotive",
            "total": 0,
            "jobs": [],
            "error": str(e)
        }
