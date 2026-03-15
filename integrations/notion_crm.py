"""
Notion CRM Integration for KeyforAgents.com
Syncs payments, leads, and subscription data to Nick James's Notion Workspace
Workspace: Nick James's Workspace
Databases: Tasks, Prompts, Projects, Integration Runs, Revenue Tracker
"""

import os
import httpx
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")  # Revenue Tracker DB
NOTION_LEADS_DB_ID = os.getenv("NOTION_LEADS_DB_ID")  # Side Hustle Ideas Pipeline
NOTION_TASKS_DB_ID = os.getenv("NOTION_TASKS_DB_ID")  # AI Agent Pro Task Tracker
NOTION_API_URL = "https://api.notion.com/v1"

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}


async def update_notion_on_payment(payment_data: dict):
    """Update Notion Revenue Tracker database on payment events"""
    event = payment_data.get("event", "unknown")
    customer_id = payment_data.get("customer_id", "")
    amount = payment_data.get("amount", 0)
    plan = payment_data.get("plan", "")
    status = payment_data.get("status", "active")

    page_data = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Name": {
                "title": [{"text": {"content": f"{event} — {customer_id}"}}]
            },
            "Amount": {
                "number": float(amount)
            },
            "Status": {
                "select": {"name": status.capitalize()}
            },
            "Plan": {
                "rich_text": [{"text": {"content": plan}}]
            },
            "Event Type": {
                "select": {"name": event.replace("_", " ").title()}
            },
            "Date": {
                "date": {"start": datetime.utcnow().isoformat()}
            },
            "Customer ID": {
                "rich_text": [{"text": {"content": customer_id}}]
            }
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{NOTION_API_URL}/pages",
            headers=HEADERS,
            json=page_data
        )
        if response.status_code == 200:
            logger.info(f"Notion updated: {event} for {customer_id}")
        else:
            logger.error(f"Notion update failed: {response.status_code} {response.text}")


async def add_lead_to_notion(lead_data: dict):
    """Add a new lead to the Side Hustle Ideas Pipeline database"""
    name = lead_data.get("name", "Unknown")
    email = lead_data.get("email", "")
    agency = lead_data.get("agency", "")
    suburb = lead_data.get("suburb", "")
    score = lead_data.get("score", 0)
    source = lead_data.get("source", "Apollo")

    page_data = {
        "parent": {"database_id": NOTION_LEADS_DB_ID},
        "properties": {
            "Name": {
                "title": [{"text": {"content": f"{name} — {agency}"}}]
            },
            "Email": {
                "email": email
            },
            "Agency": {
                "rich_text": [{"text": {"content": agency}}]
            },
            "Suburb": {
                "rich_text": [{"text": {"content": suburb}}]
            },
            "Score": {
                "number": float(score)
            },
            "Source": {
                "select": {"name": source}
            },
            "Status": {
                "select": {"name": "New Lead"}
            },
            "Date Added": {
                "date": {"start": datetime.utcnow().isoformat()}
            }
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{NOTION_API_URL}/pages",
            headers=HEADERS,
            json=page_data
        )
        if response.status_code == 200:
            logger.info(f"Lead added to Notion: {name} ({agency})")
            return response.json().get("id")
        else:
            logger.error(f"Failed to add lead: {response.text}")
            return None


async def create_task_in_notion(task_title: str, description: str, priority: str = "Medium"):
    """Create a task in the AI Agent Pro Task Tracker"""
    page_data = {
        "parent": {"database_id": NOTION_TASKS_DB_ID},
        "properties": {
            "Name": {
                "title": [{"text": {"content": task_title}}]
            },
            "Description": {
                "rich_text": [{"text": {"content": description}}]
            },
            "Priority": {
                "select": {"name": priority}
            },
            "Status": {
                "select": {"name": "Todo"}
            },
            "Created": {
                "date": {"start": datetime.utcnow().isoformat()}
            }
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{NOTION_API_URL}/pages",
            headers=HEADERS,
            json=page_data
        )
        if response.status_code == 200:
            logger.info(f"Task created in Notion: {task_title}")
        else:
            logger.error(f"Task creation failed: {response.text}")


async def query_notion_database(database_id: str, filter_params: Optional[dict] = None) -> list:
    """Query any Notion database and return results"""
    body = {}
    if filter_params:
        body["filter"] = filter_params

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{NOTION_API_URL}/databases/{database_id}/query",
            headers=HEADERS,
            json=body
        )
        if response.status_code == 200:
            return response.json().get("results", [])
        else:
            logger.error(f"Notion query failed: {response.text}")
            return []
