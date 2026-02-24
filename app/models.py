from dataclasses import dataclass


@dataclass
class Job:
    job_url: str
    title: str
    description: str
    salary: str
    location: str
    hr_email: str
    hr_linkedin: str
    source: str = "LinkedIn"