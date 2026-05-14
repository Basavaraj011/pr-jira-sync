import os
import sys
import logging

workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
sys.path.insert(0, workspace_root)

from src.plugins.jira_ticketing import ticket_creator

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

ticket_key = os.getenv("JIRA_KEY")
status = os.getenv("TICKET_STATUS")

if not ticket_key or not status:
    logging.info("Missing JIRA_KEY or TICKET_STATUS environment variables")
    sys.exit(1)

try:
    ticket_creator.change_ticket_status(ticket_key, status)
    logging.info(f"Ticket transistion is successful")
except Exception as e:
    logging.error(f"Error occurred while updating the Jira ticket {ticket_key}: {e}")
