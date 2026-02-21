import os
from dotenv import load_dotenv

from app.linkedin.runner import run
from app.output.json_writer import write_jobs_to_json
from app.storage.postgres import close_storage  # ← ДОБАВЬ

load_dotenv()

SAVE_TO_JSON = os.getenv("SAVE_TO_JSON", "false").lower() == "true"

def main() -> None:
    try:
        jobs = run()
    finally:
        close_storage()  # ← ОБЯЗАТЕЛЬНО

    if SAVE_TO_JSON:
        out_path = write_jobs_to_json(jobs, "output_linkedin.json")
        print(f"\nDone. Saved JSON: {out_path.resolve()} | jobs: {len(jobs)}")
    else:
        print(f"\nDone. Saved to PostgreSQL | jobs: {len(jobs)}")

if __name__ == "__main__":
    main()