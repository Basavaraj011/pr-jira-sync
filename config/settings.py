"""
Global settings for the Error Healing System
"""
import os
import json
from dotenv import load_dotenv

load_dotenv()
PROJECT_DB_CONFIG = json.loads(os.getenv("PROJECT_DB_CONFIG", '{ "sql_schema": "project_1", "sql_database": "AI_PredictiveRecoveryDB"}'))

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_NAME = PROJECT_DB_CONFIG["sql_database"]
DATABASE_SCHEMA = PROJECT_DB_CONFIG["sql_schema"]

# Jira Configuration
JIRA_URL = os.getenv("JIRA_URL")
JIRA_USERNAME = os.getenv("JIRA_USERNAME")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")
JIRA_ISSUE_TYPE = os.getenv("JIRA_ISSUE_TYPE")
JIRA_LABELS = os.getenv("JIRA_LABELS")
JIRA_BOARD_ID = os.getenv("JIRA_BOARD_ID")

TEAMS_WORKFLOW_URL = os.getenv("TEAMS_WORKFLOW_URL")
 