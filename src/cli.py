import argparse
from config import ConfigManager
from scraper import fetch_new_records, resume_incomplete_fetch
from logger import get_logger

logger = get_logger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Fetch Jira issues and manage checkpoints.")
    parser.add_argument("--project", required=True, help="Project key (e.g., ABC)")
    parser.add_argument("--limit", type=int, required=True, help="Number of new records to fetch")

    args = parser.parse_args()
    project_key = args.project
    new_limit = args.limit

    config = ConfigManager(project_key)
    state = config.get_state()

    logger.info(f"Starting process for project {project_key} with limit {new_limit}")
    logger.info(f"Current checkpoint state: {state}")

    if config.is_incomplete_run():
        logger.warning("Previous run was incomplete. Resuming before fetching new records.")
        resume_incomplete_fetch(project_key, config)
    else:
        logger.info("No incomplete run detected.")

    start_from = config.get_state()["last_successful_count"]
    config.update_state(last_requested_limit=new_limit, current_checkpoint=start_from + new_limit)

    try:
        fetch_new_records(project_key, start_from, new_limit, config)
        config.reset_on_success(new_limit)
        logger.info(f"Successfully fetched {new_limit} new records for project {project_key}.")
    except Exception as e:
        logger.error(f"Error during fetching new records: {e}")
        logger.warning("Saving current checkpoint for recovery on next run.")
        config.save_state()

if __name__ == "__main__":
    main()
