# 🕸️ Apache Jira Data Scraper & Transformer

## 📘 Overview
This project implements a **fault-tolerant, scalable data scraping and transformation pipeline** that extracts issue data from **Apache’s public Jira instance** and converts it into a **clean JSONL dataset** suitable for **training Large Language Models (LLMs)**.

It automatically handles pagination, retries, rate limits, and incremental checkpointing, ensuring that the process can **resume from the last saved state** without data loss.

## 🧩 Tech Stack
- **Language:** Python 3.10+
- **Libraries:** `requests`, `tqdm`, `argparse`, `json`, `os`, `logging`
- **Data Format:** JSON / JSONL
- **Environment:** Virtualenv / venv

## 🚀 Features

- Automatic Fetching: Retrieve Jira issues for multiple Apache projects via REST API.

- Incremental Updates: Maintains checkpoints to resume fetching without duplication.

- Per-Project Isolation: Each project’s data and state tracked independently.

- Data Transformation: Converts raw issue JSON into a clean JSONL structure.

- Reset Support: Reset all or specific projects (raw data, processed files, and checkpoints).

- CLI Control: Command-line arguments for batch size, limits, and project selection.

- Logging: Detailed logs to monitor fetch and transform progress.

## 🏗️ Project Structure
```bash 
Scaler/
├── main.py                # CLI entry point for pipeline
├── src/
│   ├── scraper.py         # Handles Jira API fetching
│   ├── transformer.py     # Handles data cleaning and conversion
│   ├── config.py          # Paths, constants, and global config
│   ├── utils.py           # Helper functions (if any)
│   └── ...
├── outputs/
│   ├── raw/               # Raw JSON issues per project
│   ├── processed/         # Cleaned JSONL output per project
│   └── checkpoints.json   # Stores project fetch state
└── requirements.txt
```

##  ⚙️ Installation and Setup 
### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/scaler-jira-pipeline.git
cd Scaler
```
### 2. Create Virtual Environment
```bash
python3 -m venv scaler_project
source scaler_project/bin/activate
```
### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

## 🧑‍💻 Usage 
- Fetch and transform all projects, by default it fetches data for: SPARK, HADOOP, HIVE
```bash
  python main.py
```

- Fetch specific/multiple projects

```bash
python main.py --projects HIVE SPARK
```

- Fetch limited new issues per project

```bash
python main.py --projects SPARK --limit 20
```

- Change batch size (Fetches issues in batches per API call)
```bash
python main.py --batch-size 20 --projects SPARK --limit 200
```

### 🧹 Example Output:
```bash
(scaler_project) ayush:Scaler ayushkumar$ python main.py --batch-size 20 --projects SPARK --limit 200
🚀 Starting data fetch for projects: SPARK (limit per project: 200)
2025-11-02 15:11:32,739 — INFO — src.scraper — Starting project SPARK
2025-11-02 15:11:32,739 — INFO — Starting project SPARK
2025-11-02 15:11:32,739 — INFO — src.scraper — Added 200 pending for SPARK (now pending=200)
2025-11-02 15:11:32,739 — INFO — Added 200 pending for SPARK (now pending=200)
2025-11-02 15:11:32,740 — INFO — src.scraper — Fetching SPARK startAt=0 (batch=20) pending=200 total_fetched=0
2025-11-02 15:11:32,740 — INFO — Fetching SPARK startAt=0 (batch=20) pending=200 total_fetched=0
2025-11-02 15:11:37,372 — INFO — src.scraper — Fetching SPARK startAt=20 (batch=20) pending=180 total_fetched=20
2025-11-02 15:11:37,372 — INFO — Fetching SPARK startAt=20 (batch=20) pending=180 total_fetched=20
2025-11-02 15:11:41,090 — INFO — src.scraper — Fetching SPARK startAt=40 (batch=20) pending=160 total_fetched=40
2025-11-02 15:11:41,090 — INFO — Fetching SPARK startAt=40 (batch=20) pending=160 total_fetched=40
2025-11-02 15:11:45,148 — INFO — src.scraper — Fetching SPARK startAt=60 (batch=20) pending=140 total_fetched=60
2025-11-02 15:11:45,148 — INFO — Fetching SPARK startAt=60 (batch=20) pending=140 total_fetched=60
2025-11-02 15:11:48,880 — INFO — src.scraper — Fetching SPARK startAt=80 (batch=20) pending=120 total_fetched=80
2025-11-02 15:11:48,880 — INFO — Fetching SPARK startAt=80 (batch=20) pending=120 total_fetched=80
2025-11-02 15:11:53,598 — INFO — src.scraper — Fetching SPARK startAt=100 (batch=20) pending=100 total_fetched=100
2025-11-02 15:11:53,598 — INFO — Fetching SPARK startAt=100 (batch=20) pending=100 total_fetched=100
2025-11-02 15:11:57,752 — INFO — src.scraper — Fetching SPARK startAt=120 (batch=20) pending=80 total_fetched=120
2025-11-02 15:11:57,752 — INFO — Fetching SPARK startAt=120 (batch=20) pending=80 total_fetched=120
2025-11-02 15:12:02,323 — INFO — src.scraper — Fetching SPARK startAt=140 (batch=20) pending=60 total_fetched=140
2025-11-02 15:12:02,323 — INFO — Fetching SPARK startAt=140 (batch=20) pending=60 total_fetched=140
2025-11-02 15:12:06,899 — INFO — src.scraper — Fetching SPARK startAt=160 (batch=20) pending=40 total_fetched=160
2025-11-02 15:12:06,899 — INFO — Fetching SPARK startAt=160 (batch=20) pending=40 total_fetched=160
2025-11-02 15:12:13,229 — INFO — src.scraper — Fetching SPARK startAt=180 (batch=20) pending=20 total_fetched=180
2025-11-02 15:12:13,229 — INFO — Fetching SPARK startAt=180 (batch=20) pending=20 total_fetched=180
2025-11-02 15:12:17,630 — INFO — src.scraper — Cleared pending for SPARK (fetched this run).
2025-11-02 15:12:17,630 — INFO — Cleared pending for SPARK (fetched this run).
2025-11-02 15:12:17,631 — INFO — src.scraper — Finished project SPARK (total_fetched=200 pending=0 start_at=200)
2025-11-02 15:12:17,631 — INFO — Finished project SPARK (total_fetched=200 pending=0 start_at=200)

🔄 Transforming raw data into JSONL format...
🔄 Transforming 200 new issues from SPARK...
SPARK new issues: 100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████| 200/200 [00:00<00:00, 4067.18issue/s]
✅ Appended 200 new issues for SPARK → outputs/processed/SPARK.jsonl
✅ Transformation complete! JSONL files saved in outputs/processed/
```

- Reset all data
Deletes raw, processed, and checkpoint files for all projects.
```bash
python main.py --reset
```

- Reset specific projects removes only selected projects from outputs raw/processed and checkpoints.json
```bash
python main.py --reset --projects HADOOP
```

### 🧹 Example Output:
```bash
🧹 Resetting selected projects: SPARK
🗑️ Deleted folder /Users/ayushkumar/Desktop/Academics/Coding/Scaler/outputs/raw/SPARK
🗑️ Deleted file /Users/ayushkumar/Desktop/Academics/Coding/Scaler/outputs/processed/SPARK.jsonl
🗑️ Updated checkpoints.json to remove selected projects.
✅ Selected project reset complete.
```

### Raw fetched JSON files storage:
```bash
outputs/raw/SPARK/SPARK-12345.json
```

### Processed JSONL files storage:
```bash
outputs/processed/SPARK.jsonl
```

Each line in the .jsonl file represents one issue, containing cleaned and normalized fields like:
```json
{"id": "12704979", "key": "SPARK-462", "project": "SPARK", "title": "Add APIs to Serializer for streams of objects of the same type", "description": "This could be a substantial optimization for faster serializers, because they wouldn't need to encode (and later decode) the class of each object in the stream repeatedly.", "status": "Resolved", "priority": null, "assignee": null, "reporter": "Matei Alexandru Zaharia", "labels": [], "created": "0011-07-22T23:47:00.000+0000", "updated": "2012-10-22T14:55:33.797+0000", "comments": ["Github comment from mateiz: Done in dev branch.", "Imported from Github issue spark-74, originally reported by mateiz"], "tasks": {"summarization": "Summarize the issue titled 'Add APIs to Serializer for streams of objects of the same type'", "classification": "Classify the type of issue: Bug", "qna": "Question: What is the issue about?\nAnswer: This could be a substantial optimization for faster serializers, because they wouldn't need to encode (and later decode) the class of each object in the stream repeatedly."}}
```

## 🧠 Checkpoints Explained - Checkpoints.json tracks the state of each project:
```json
{
  "SPARK": {
    "start_at": 10,
    "pending": 0,
    "total_fetched": 10,
    "last_status": "success"
  },
  "HADOOP": {
    "start_at": 10,
    "pending": 0,
    "total_fetched": 10,
    "last_status": "success"
  }
}
```
| Field             | Description                                                                   |
| ----------------- | ----------------------------------------------------------------------------- |
| **start_at**      | The API offset from where the next batch of issues will be fetched.           |
| **pending**       | The number of issues still remaining to fetch in the current run.             |
| **total_fetched** | The total number of issues successfully retrieved so far.                     |
| **last_status**   | The result of the last fetch attempt (`success`, `failed`, or `in_progress`). |


## 🧰 Command Reference

| Command              | Description                             |
| -------------------- | --------------------------------------- |
| `--projects`         | Specify one or more project keys        |
| `--limit`            | Maximum new issues to fetch per project |
| `--batch-size`       | Number of issues per API call           |
| `--reset`            | Delete outputs & checkpoints            |
| `--reset --projects` | Reset specific projects only            |


## 💡 Future Improvements
- Add multi-threaded fetching for faster performance.
- Add visualization dashboard for fetched issues.
- Export processed data to CSV or Parquet for analysis.

## Acknowledgements
Special thanks to the Apache Foundation for providing open public Jira data. Developed by Ayush Kumar as part of Scaler’s Web Scraping & Data Engineering assignment.
