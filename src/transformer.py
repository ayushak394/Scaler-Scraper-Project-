import json
from pathlib import Path
from tqdm import tqdm
from .config import RAW_DIR

OUTPUT_DIR = Path("outputs/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def transform_issue(issue_data):
    """
    Convert a raw Jira issue JSON into a structured record.
    Handles missing or null fields gracefully.
    """
    fields = issue_data.get("fields") or {}

    project_data = fields.get("project") or {}
    status_data = fields.get("status") or {}
    priority_data = fields.get("priority") or {}
    assignee_data = fields.get("assignee") or {}
    reporter_data = fields.get("reporter") or {}
    issue_type_data = fields.get("issuetype") or {}
    comment_data = (fields.get("comment") or {}).get("comments", []) or []

    return {
        "id": issue_data.get("id"),
        "key": issue_data.get("key"),
        "project": project_data.get("key"),
        "title": fields.get("summary") or "",
        "description": fields.get("description") or "",
        "status": status_data.get("name"),
        "priority": priority_data.get("name"),
        "assignee": assignee_data.get("displayName"),
        "reporter": reporter_data.get("displayName"),
        "labels": fields.get("labels") or [],
        "created": fields.get("created"),
        "updated": fields.get("updated"),
        "comments": [c.get("body", "") for c in comment_data],
        "tasks": {
            "summarization": f"Summarize the issue titled '{fields.get('summary') or 'Untitled'}'",
            "classification": f"Classify the type of issue: {issue_type_data.get('name') or 'Unknown'}",
            "qna": f"Question: What is the issue about?\nAnswer: {fields.get('description') or 'No description provided.'}"
        }
    }


def transform_projects(projects):
    """
    Incrementally transform only new raw issue files for each project.
    """
    for project in projects:
        project_dir = RAW_DIR / project
        if not project_dir.exists():
            print(f"⚠️ No raw data found for project {project}, skipping.")
            continue

        output_file = OUTPUT_DIR / f"{project}.jsonl"

        # Load already processed keys to skip duplicates
        processed_keys = set()
        if output_file.exists():
            with open(output_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        issue = json.loads(line)
                        processed_keys.add(issue.get("key"))
                    except Exception:
                        continue

        # Identify new files to process
        new_files = [
            file_path for file_path in project_dir.glob("*.json")
            if file_path.stem not in processed_keys
        ]

        if not new_files:
            print(f"✅ No new issues to transform for {project}.")
            continue

        print(f"🔄 Transforming {len(new_files)} new issues from {project}...")

        with open(output_file, "a", encoding="utf-8") as out_f:
            for file_path in tqdm(new_files, desc=f"{project} new issues", unit="issue"):
                try:
                    data = json.loads(file_path.read_text(encoding="utf-8"))
                    transformed = transform_issue(data)
                    out_f.write(json.dumps(transformed, ensure_ascii=False) + "\n")
                except Exception as e:
                    print(f"❌ Failed to transform {file_path.name}: {e}")

        print(f"✅ Appended {len(new_files)} new issues for {project} → {output_file}")
