from dataclasses import dataclass


@dataclass
class Job:
    title: str
    description: str
    salary: str
    location: str
    contact: str
    source: str = "LinkedIn"
