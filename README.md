# 🕸️ Apache Jira Data Scraper & Transformer

## 📘 Overview
This project implements a **fault-tolerant, scalable data scraping and transformation pipeline** that extracts issue data from **Apache’s public Jira instance** and converts it into a **clean JSONL dataset** suitable for **training Large Language Models (LLMs)**.

It automatically handles pagination, retries, rate limits, and incremental checkpointing, ensuring that the process can **resume from the last saved state** without data loss.

## 🎯 Objective
Build a system that:
- Scrapes issues, comments, and metadata from Apache’s public Jira projects.
- Handles failures and rate limits gracefully.
- Transforms raw data into a structured JSONL format ready for LLM training.
- Supports resumable, incremental, and efficient data collection.

## 🏗️ Architecture Overview

### 1. **Scraper Module (`src/scraper.py`)**
- Fetches issues using the **Apache JIRA REST API**.
- Handles:
  - Pagination (`startAt`, `maxResults`)
  - Network retries and timeouts
  - HTTP 429 (rate limit) and 5xx error backoff
- Saves each issue as a separate raw JSON file under: outputs/raw/<PROJECT>/

### 2. **Checkpoint System**
- Progress is tracked in: state/checkpoints.json
  Example:
```json
{"SPARK": 150, "HADOOP": 100, "HIVE": 200}
```

If the scraper stops, it resumes from the last checkpoint automatically.

Use --reset flag to clear progress:

```bash
python main.py --reset
```

### 3. Transformer Module (src/transformer.py)
- Converts each raw issue into a structured JSONL format.

- Safely handles missing fields or malformed data.

- Generates three derived LLM tasks - Summarization, Classification, Q&A

### 4. Output Format
Each issue is stored as one line in: outputs/processed/<PROJECT>.jsonl

Example: 
```json
{
  "id": "12328268",
  "key": "HADOOP-12",
  "project": "HADOOP",
  "title": "InputFormat used in job must be in JobTracker classpath",
  "description": "...",
  "status": "Closed",
  "priority": "Minor",
  "assignee": null,
  "reporter": "Bryan Pendleton",
  "labels": [],
  "created": "2006-01-31T07:00:17.000+0000",
  "updated": "2009-07-08T16:51:40.421+0000",
  "comments": [
    "We've thus far avoided loading job-specific code...",
    "Wouldn't it be appropriate to make input splitting into a task..."
  ],
  "tasks": {
    "summarization": "Summarize the issue titled 'InputFormat used in job must be in JobTracker classpath'",
    "classification": "Classify the type of issue: Bug",
    "qna": "Question: What is the issue about?\nAnswer: During development, I've been creating/tweaking custom InputFormat implementations..."
  }
}
```

#  Installation and Setup 
### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/apache-jira-scraper.git
cd Scaler
```
### 2. Create Virtual Environment
```bash
python -m venv scaler_project
source scaler_project/bin/activate  # On Windows: scaler_project\Scripts\activate
```
### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
### 4. Run the Scraper
```bash
python main.py
```

### 5. Optional: Reset State
```bash
python main.py --reset
```

# 🧩 How Requirements Are Achieved

| Requirement                    | Implementation                            | Status |
| ------------------------------ | ----------------------------------------- | ------ |
| Fetch issues/comments/metadata | JIRA REST API via `requests`              | ✅      |
| Handle pagination              | `startAt` and `maxResults`                | ✅      |
| Resume from last state         | `state/checkpoints.json`                  | ✅      |
| Handle retries/timeouts        | Retry loop with exponential backoff       | ✅      |
| Handle 429 and 5xx             | Sleep + retry mechanism                   | ✅      |
| Handle malformed data          | Safe `.get()` accessors                   | ✅      |
| Convert to JSONL               | `transform_issue()`                       | ✅      |
| Include metadata/comments      | Flattened into structured format          | ✅      |
| Derived LLM tasks              | Summarization, classification, QnA        | ✅      |
| Optimization                   | Checkpoints, limit flag, incremental runs | ✅      |
| Fault tolerance                | Recovery through checkpointing            | ✅      |


# 🚀 Optimization and Reliability

### ✅ Efficiency

- Limit flag to fetch only first N issues during testing.

- Batch-based pagination reduces API calls.

- Raw/processed separation prevents reprocessing.

### ✅ Reliability

- Checkpointing ensures resumability.

- Retries and timeouts avoid crashes.

- Graceful fallbacks for missing or malformed data.

# 🧠 Design Decisions

| Decision                      | Reason                                                       |
| ----------------------------- | ------------------------------------------------------------ |
| Used Apache JIRA REST API     | Avoided HTML scraping, ensured structured JSON data.         |
| Stored individual issue files | Enables incremental processing and debugging.                |
| JSONL for processed output    | Directly usable for LLM datasets.                            |
| Checkpoint system             | Prevents redundant network calls and ensures recoverability. |
| Derived tasks generation      | Adds practical LLM fine-tuning use cases.                    |

# 🧪 Testing
- Verified correctness by running incremental fetches (limit 5 → 8 → 50).  
- Confirmed checkpoint updates and resumability after interruptions.  
- Validated transformation schema and JSONL output integrity.

# ⚡ Future Improvements

- Add multiprocessing for parallel scraping.

- Cache responses locally using requests-cache.

- Add CLI arguments for custom project selection.

- Integrate a validation layer to skip corrupted JSON files.


# 🏁 Acknowledgments

Special thanks to the Apache Foundation for providing open public Jira data.
Developed as part of the Scaler Web Scraping Tutor Assignment.
