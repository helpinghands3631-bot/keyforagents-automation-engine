"""KeyForAgents Lead Agent - AI-powered lead qualification and automation"""
import os
import asyncio
import logging
from datetime import datetime
from typing import Optional
import httpx
from notion_client import AsyncClient as NotionClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_LEADS_DB = os.getenv("NOTION_LEADS_DB", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
API_BASE_URL = os.getenv("API_BASE_URL", "https://keyforagents.com/api")

notion = NotionClient(auth=NOTION_TOKEN)


class LeadAgent:
    """AI agent for lead qualification and routing."""

    def __init__(self):
        self.qualified_count = 0
        self.rejected_count = 0

    async def fetch_new_leads(self):
        """Fetch unprocessed leads from Notion database."""
        try:
            response = await notion.databases.query(
                database_id=NOTION_LEADS_DB,
                filter={
                    "property": "Status",
                    "select": {"equals": "New"}
                }
            )
            return response.get("results", [])
        except Exception as e:
            logger.error(f"Failed to fetch leads: {e}")
            return []

    def qualify_lead(self, lead: dict) -> tuple[bool, str]:
        """Score and qualify a lead based on properties."""
        props = lead.get("properties", {})

        name = self._get_text(props, "Name")
        email = self._get_email(props, "Email")
        budget = self._get_number(props, "Budget")
        source = self._get_text(props, "Source")
        interest = self._get_text(props, "Interest")

        score = 0
        reasons = []

        if email and "@" in email:
            score += 30
        else:
            return False, "Missing valid email"

        if budget and budget >= 1000:
            score += 40
            reasons.append(f"Budget ${budget:,.0f}")
        elif budget and budget >= 500:
            score += 20
            reasons.append(f"Budget ${budget:,.0f} (low)")

        if source in ["referral", "website", "keyforagents.com"]:
            score += 20
            reasons.append(f"Quality source: {source}")

        if interest and len(interest) > 20:
            score += 10
            reasons.append("Detailed interest noted")

        qualified = score >= 60
        summary = f"Score {score}/100 | " + " | ".join(reasons) if reasons else f"Score {score}/100"
        return qualified, summary

    async def update_lead_status(self, page_id: str, status: str, notes: str):
        """Update lead status in Notion."""
        try:
            await notion.pages.update(
                page_id=page_id,
                properties={
                    "Status": {"select": {"name": status}},
                    "Agent Notes": {"rich_text": [{"text": {"content": notes[:2000]}}]},
                    "Processed At": {"date": {"start": datetime.utcnow().isoformat()}}
                }
            )
        except Exception as e:
            logger.error(f"Failed to update lead {page_id}: {e}")

    async def notify_telegram(self, message: str):
        """Send notification via Telegram."""
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            return
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        async with httpx.AsyncClient() as client:
            try:
                await client.post(url, json={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": message,
                    "parse_mode": "HTML"
                })
            except Exception as e:
                logger.error(f"Telegram error: {e}")

    async def trigger_onboarding(self, lead: dict):
        """Trigger automated onboarding workflow via API."""
        props = lead.get("properties", {})
        payload = {
            "email": self._get_email(props, "Email"),
            "name": self._get_text(props, "Name"),
            "source": self._get_text(props, "Source"),
            "triggered_at": datetime.utcnow().isoformat()
        }
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    f"{API_BASE_URL}/onboard",
                    json=payload,
                    timeout=10
                )
                resp.raise_for_status()
                logger.info(f"Onboarding triggered for {payload['email']}")
            except Exception as e:
                logger.error(f"Onboarding failed: {e}")

    async def process_lead(self, lead: dict):
        """Process a single lead: qualify, update, notify."""
        page_id = lead["id"]
        props = lead.get("properties", {})
        name = self._get_text(props, "Name") or "Unknown"
        email = self._get_email(props, "Email") or "no-email"

        qualified, summary = self.qualify_lead(lead)

        if qualified:
            self.qualified_count += 1
            await self.update_lead_status(page_id, "Qualified", summary)
            await self.trigger_onboarding(lead)
            msg = (
                f"<b>New Qualified Lead</b>\n"
                f"Name: {name}\n"
                f"Email: {email}\n"
                f"{summary}"
            )
            await self.notify_telegram(msg)
            logger.info(f"QUALIFIED: {name} ({email}) - {summary}")
        else:
            self.rejected_count += 1
            await self.update_lead_status(page_id, "Rejected", summary)
            logger.info(f"REJECTED: {name} ({email}) - {summary}")

    async def run_cycle(self):
        """Run one full processing cycle."""
        leads = await self.fetch_new_leads()
        logger.info(f"Found {len(leads)} new leads")
        tasks = [self.process_lead(lead) for lead in leads]
        await asyncio.gather(*tasks)
        logger.info(f"Cycle complete: {self.qualified_count} qualified, {self.rejected_count} rejected")

    async def run_forever(self, interval_seconds: int = 300):
        """Run agent in continuous loop."""
        logger.info("Lead Agent started — polling every %ds", interval_seconds)
        while True:
            try:
                await self.run_cycle()
            except Exception as e:
                logger.error(f"Cycle error: {e}")
            await asyncio.sleep(interval_seconds)

    @staticmethod
    def _get_text(props: dict, key: str) -> Optional[str]:
        try:
            items = props[key]["title"] or props[key]["rich_text"]
            return items[0]["plain_text"] if items else None
        except (KeyError, IndexError):
            return None

    @staticmethod
    def _get_email(props: dict, key: str) -> Optional[str]:
        try:
            return props[key]["email"]
        except KeyError:
            return None

    @staticmethod
    def _get_number(props: dict, key: str) -> Optional[float]:
        try:
            return props[key]["number"]
        except KeyError:
            return None


if __name__ == "__main__":
    agent = LeadAgent()
    asyncio.run(agent.run_forever(interval_seconds=300))
