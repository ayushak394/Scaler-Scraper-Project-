from src.scraper import Scraper
from src.transformer import transform_projects
from src.config import OUTPUT_DIR, STATE_FILE
import logging
import argparse
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Apache Jira Data Pipeline")
    parser.add_argument(
        "--projects",
        nargs="+",
        default=["SPARK", "HADOOP", "HIVE"],
        help="List of Apache Jira project keys to scrape",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of issues to fetch per project (optional)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Number of issues to fetch per API call (optional)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete outputs/raw, outputs/processed and state/checkpoints.json before running",
    )

    args = parser.parse_args()

    # --- Reset handler ---
    if args.reset:
        print("🧹 Resetting outputs and checkpoints...")
        shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
        (OUTPUT_DIR / "raw").mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "processed").mkdir(parents=True, exist_ok=True)
        try:
            STATE_FILE.unlink()
        except FileNotFoundError:
            pass
        print("✅ Reset complete.\n")

    else:

        print(f"🚀 Starting data fetch for projects: {', '.join(args.projects)} (limit: {args.limit})")

        # Initialize and run the scraper
        scraper = Scraper(args.projects, max_issues=args.limit, batch_size=args.batch_size)
        scraper.run()

        # Run transformation automatically after scraping
        print("\n🔄 Transforming raw data into JSONL format...")
        try:
            transform_projects(args.projects)
            print("✅ Transformation complete! JSONL files are saved in outputs/processed/")
        except Exception as e:
            logging.error(f"Data transformation failed: {e}")
            print("❌ Transformation failed. Check logs for details.")


if __name__ == "__main__":
    main()
