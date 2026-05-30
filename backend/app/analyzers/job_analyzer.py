from collections import Counter

def analyze_jobs(jobs: list) -> dict:
    """
    Analyze a list of job dicts and return intelligence insights.
    """
    if not jobs:
        return {}

    # Flatten all skills
    all_skills = []
    for job in jobs:
        skills = job.get("skills", [])
        if isinstance(skills, list):
            all_skills.extend([s.lower().strip() for s in skills if s])

    skill_counts = Counter(all_skills)
    top_skills = [
        {"skill": skill, "count": count}
        for skill, count in skill_counts.most_common(20)
    ]

    companies = [job.get("company", "") for job in jobs if job.get("company")]
    company_counts = Counter(companies)
    top_companies = [
        {"company": company, "count": count}
        for company, count in company_counts.most_common(10)
    ]

    job_types = [job.get("job_type", "unknown") for job in jobs]
    job_type_counts = Counter(job_types)
    job_type_breakdown = [
        {"type": jtype, "count": count}
        for jtype, count in job_type_counts.most_common()
    ]

    locations = [job.get("location", "").strip() for job in jobs if job.get("location")]
    location_counts = Counter(locations)
    top_locations = [
        {"location": loc, "count": count}
        for loc, count in location_counts.most_common(10)
    ]

    categories = [job.get("category", "").strip() for job in jobs if job.get("category")]
    category_counts = Counter(categories)
    category_breakdown = [
        {"category": cat, "count": count}
        for cat, count in category_counts.most_common(10)
    ]

    salaries = [job.get("salary") for job in jobs if job.get("salary")]

    return {
        "total_jobs_analyzed": len(jobs),
        "top_skills": top_skills,
        "top_companies": top_companies,
        "job_type_breakdown": job_type_breakdown,
        "top_locations": top_locations,
        "category_breakdown": category_breakdown,
        "jobs_with_salary": len(salaries),
        "salary_samples": salaries[:10]
    }
