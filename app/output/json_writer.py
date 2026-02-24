import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, Union

from app.models import Job


def write_jobs_to_json(jobs: Iterable[Job], path: Union[str, Path] = "output_linkedin.json") -> Path:
    out_path = Path(path)
    out_path.write_text(
        json.dumps([asdict(j) for j in jobs], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return out_path


