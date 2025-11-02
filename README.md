# 🧠 Apache Jira Scraper — Web Scraping Tutor Assignment

## 📘 Overview
This project is a data scraping and transformation pipeline that extracts **public issue data from Apache’s Jira instance** and converts it into a structured dataset suitable for **training Large Language Models (LLMs)**.

The scraper handles:
- Pagination and rate limits
- Network errors and retries
- Checkpoint-based resuming
- Data transformation into clean JSONL format

---

## 🚀 Features
✅ Fetches issues, metadata, and comments from Apache Jira  
✅ Resumable scraping via checkpoints  
✅ Handles malformed or missing data gracefully  
✅ Converts raw issues into structured LLM-ready JSONL  
✅ Modular design: `jira_client`, `scraper`, `transformer`, `utils`

---