from src.scraper import Scraper
from src.transformer import transform_projects
from src.config import OUTPUT_DIR, STATE_FILE
from pathlib import Path

import logging
import argparse
import shutil
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s — %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

def reset_all():
    """Delete all output folders and checkpoint file."""
    print("🧹 Performing full reset (all projects)...")
    shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
    (OUTPUT_DIR / "raw").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "processed").mkdir(parents=True, exist_ok=True)
    try:
        Path(STATE_FILE).unlink()
    except FileNotFoundError:
        pass
    print("✅ All projects and checkpoints cleared.\n")



def reset_selected_projects(projects):
    """Delete only specific projects from outputs and checkpoint."""
    print(f"🧹 Resetting selected projects: {', '.join(projects)}")

    for p in projects:
        for folder in ["raw", "processed"]:
            folder_path = OUTPUT_DIR / folder
            deleted_any = False

            for path in folder_path.glob(f"{p}*"):
                if path.is_file():
                    path.unlink()
                    print(f"🗑️ Deleted file {path}")
                    deleted_any = True
                elif path.is_dir():
                    shutil.rmtree(path)
                    print(f"🗑️ Deleted folder {path}")
                    deleted_any = True

            if not deleted_any:
                print(f"⚠️ No {folder} files or folders found for {p}")

    if Path(STATE_FILE).exists():
        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f)

            modified = False

            for p in projects:
                if p in data:
                    del data[p]
                    modified = True

            if "projects" in data:
                for p in projects:
                    if p in data["projects"]:
                        del data["projects"][p]
                        modified = True

            if modified:
                with open(STATE_FILE, "w") as f:
                    json.dump(data, f, indent=2)
                print("🗑️ Updated checkpoints.json to remove selected projects.")
            else:
                print("ℹ️ No checkpoint entries found for selected projects.")

        except json.JSONDecodeError:
            print("⚠️ Checkpoints file corrupted or empty. Skipping edit.")

    (OUTPUT_DIR / "raw").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "processed").mkdir(parents=True, exist_ok=True)

    print("✅ Selected project reset complete.\n")


def main():
    parser = argparse.ArgumentParser(description="Apache Jira Data Pipeline")
    parser.add_argument(
        "--projects",
        nargs="+",
        default=None,
        help="List of Apache Jira project keys (e.g., SPARK HADOOP HIVE)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of NEW issues to fetch per project (optional)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Number of issues per API call (default: 50)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete outputs and checkpoints. Optionally use with --projects to reset only specific projects.",
    )

    args = parser.parse_args()

    if args.reset:
        if args.projects:
            reset_selected_projects(args.projects)
        else:
            reset_all()
        return  

    projects = args.projects or ["SPARK", "HADOOP", "HIVE"]
    print(f"🚀 Starting data fetch for projects: {', '.join(projects)} (limit per project: {args.limit})")

    add_map = {p: args.limit for p in projects} if args.limit else {}
    scraper = Scraper(projects, max_issues=None, batch_size=args.batch_size)
    scraper.run(add_pending_per_project=add_map)

    print("\n🔄 Transforming raw data into JSONL format...")
    try:
        transform_projects(projects)
        print("✅ Transformation complete! JSONL files saved in outputs/processed/")
    except Exception as e:
        logger.error("❌ Data transformation failed: %s", e)
        print("❌ Transformation failed. Check logs for details.")


if __name__ == "__main__":
    main()
