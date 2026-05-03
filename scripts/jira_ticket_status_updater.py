import os, sys

workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
sys.path.insert(0, workspace_root)

from src.plugins.jira_ticketing import ticket_creator

ticket_key = os.getenv("JIRA_KEY")
status = os.getenv("TICKET_STATUS")

ticket_creator.change_ticket_status(ticket_key, status)
