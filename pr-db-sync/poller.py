import os, sys
import json
import time
import yaml
import requests
from datetime import datetime

from database.database_operations import upsert_pr_metadata
from connections.database_connections import DatabaseManager
from config.settings import DATABASE_URL

# -------------------------
# Configuration & Constants
# -------------------------
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
sys.path.insert(0, workspace_root)

CONFIG = yaml.safe_load(open(f"{workspace_root}/config/teams.yml"))
PROCESSED_FILE = f"{workspace_root}/pr-db-sync/processed.json"

GITHUB_API = "https://api.github.com"
GITHUB_TOKEN = "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"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

POLL_INTERVAL = CONFIG.get("poll_interval_seconds", 120)

# -------------------------
# State handling
# -------------------------

def load_processed():
    if not os.path.exists(PROCESSED_FILE):
        return set()
    return set(json.load(open(PROCESSED_FILE))["processed"])

def save_processed(processed):
    json.dump({"processed": list(processed)}, open(PROCESSED_FILE, "w"), indent=2)

# -------------------------
# GitHub API
# -------------------------

def fetch_pull_requests(owner, repo):
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls"
    params = {"state": "all", "per_page": 100}
    resp = requests.get(url, headers=HEADERS, params=params)
    resp.raise_for_status()
    return resp.json()

def fetch_reviews(owner, repo, pr_number):
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

# -------------------------
# Domain logic
# -------------------------

def extract_jira_key(text):
    # Simple pattern, adjust if needed
    import re
    m = re.search(r"[A-Z]+-\d+", text)
    return m.group(0) if m else None

def is_approved(reviews):
    return any(r["state"] == "APPROVED" for r in reviews)

def pr_status(pr, approved):
    if pr["draft"]:
        return "Draft"
    if pr["state"] == "open":
        return "Approved" if approved else "Open"
    if pr["state"] == "closed":
        if pr.get("merged_at"):
            return "Merged and Closed"
        return "Closed"
    return "In Progress"

# -------------------------
# DB update
# -------------------------

def update_database(pr, status, reviews):
    db = DatabaseManager(DATABASE_URL)
    approved_review = next((r for r in reviews if r["state"] == "APPROVED"), None)
    meta = {
        "jira_key": extract_jira_key(pr["title"]) or extract_jira_key(pr["head"]["ref"]),
        "repo": f"{pr['base']['repo']['owner']['login']}/{pr['base']['repo']['name']}",
        "pr_number": pr["number"],
        "pr_url": pr["html_url"],
        "title": pr["title"],
        "branch": pr["head"]["ref"],
        "base_branch": pr["base"]["ref"],
        "status": status,
        "approved_at": approved_review["submitted_at"] if approved_review else None,
        "merged_at": pr.get("merged_at"),
        "closed_at": pr.get("closed_at"),
        "created_at": pr.get("created_at"),
        "updated_at": pr.get("updated_at")
    }

    if not meta["jira_key"]:
        return  # PR not linked to Jira → ignored

    upsert_pr_metadata(meta, db)

# -------------------------
# Main poller loop
# -------------------------

def poll_once(owner, repo, processed):
    prs = fetch_pull_requests(owner, repo)

    for pr in prs:
        reviews = fetch_reviews(owner, repo, pr["number"])
        approved = is_approved(reviews)

        status = pr_status(pr, approved)

        event_key = f"{repo}:{pr['number']}:{status}:{pr['updated_at']}"
        if event_key in processed:
            continue

        update_database(pr, status, reviews)
        processed.add(event_key)

def main():
    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN is not set")

    owner = 'Basavaraj011'
    repo = 'error_pipeline_demo'

    processed = load_processed()
    poll_once(owner, repo, processed)
    save_processed(processed)

if __name__ == "__main__":
    main()
    # owner = 'Basavaraj011'
    # repo = 'error_pipeline_demo'
    # prs = fetch_pull_requests(owner=owner, repo=repo)

    # for pr in prs:
    #     reviews = fetch_reviews(owner, repo, pr["number"])
    #     approved = is_approved(reviews)

    #     status = pr_status(pr, approved)
    #     meta = {
    #     "jira_key": extract_jira_key(pr["title"]) or extract_jira_key(pr["head"]["ref"]),
    #     "repo": f"{pr['base']['repo']['owner']['login']}/{pr['base']['repo']['name']}",
    #     "pr_number": pr["number"],
    #     "pr_url": pr["html_url"],
    #     "title": pr["title"],
    #     "branch": pr["head"]["ref"],
    #     "base_branch": pr["base"]["ref"],
    #     "status": status,
    #     "approved_at": datetime.utcnow() if status == "Approved" else None,
    #     "merged_at": datetime.utcnow() if status == "Merged and Closed" else None,
    #     "reopened_at": datetime.utcnow() if status == "Reopened" else None
    #     }

    #     print(meta)