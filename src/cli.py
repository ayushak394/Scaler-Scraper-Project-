import argparse
from .scraper import Scraper
from .transformer import transform_project
from .logger import get_logger

logger = get_logger(__name__)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--projects", "-p", nargs="+", help="Project keys (e.g., HADOOP HIVE SPARK)", default=["HADOOP","HIVE","SPARK"])
    parser.add_argument("--transform", "-t", action="store_true", help="Run transformation after scraping")
    args = parser.parse_args()

    s = Scraper(args.projects)
    s.run()
    if args.transform:
        for p in args.projects:
            try:
                transform_project(p)
            except Exception as e:
                logger.error("Transform failed for %s: %s", p, e)

if __name__ == "__main__":
    main()
