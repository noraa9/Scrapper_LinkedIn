from dataclasses import dataclass


@dataclass
class Job:
<<<<<<< HEAD
    job_url: str
=======
>>>>>>> 91975673bd3d2a8a367df3cae94571db7f11373e
    title: str
    description: str
    salary: str
    location: str
<<<<<<< HEAD
    hr_email: str
    hr_linkedin: str
    source: str = "LinkedIn"
=======
    contact: str
    source: str = "LinkedIn"
>>>>>>> 91975673bd3d2a8a367df3cae94571db7f11373e
