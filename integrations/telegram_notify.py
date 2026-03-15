"""
Telegram Notification Integration for KeyforAgents.com
Sends real-time alerts for payments, new leads, agent events and system status
"""

import os
import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


async def send_telegram_alert(message: str, parse_mode: str = "HTML") -> bool:
    """Send a Telegram message to the configured chat"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram not configured, skipping alert")
        return False

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": f"<b>KeyforAgents.com</b>\n\n{message}",
        "parse_mode": parse_mode
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{TELEGRAM_API}/sendMessage",
                json=payload,
                timeout=10.0
            )
            if response.status_code == 200:
                logger.info(f"Telegram alert sent: {message[:50]}...")
                return True
            else:
                logger.error(f"Telegram failed: {response.status_code} {response.text}")
                return False
        except Exception as e:
            logger.error(f"Telegram exception: {e}")
            return False


async def send_revenue_report(total_today: float, total_month: float, active_subs: int):
    """Send daily revenue summary to Telegram"""
    message = (
        f"DAILY REVENUE REPORT\n"
        f"Today: AUD${total_today:.2f}\n"
        f"This Month: AUD${total_month:.2f}\n"
        f"Active Subscriptions: {active_subs}\n"
        f"Platform: KeyforAgents.com"
    )
    await send_telegram_alert(message)


async def send_new_lead_alert(name: str, agency: str, suburb: str, score: int):
    """Alert when a high-value lead is found"""
    message = (
        f"NEW LEAD DETECTED\n"
        f"Name: {name}\n"
        f"Agency: {agency}\n"
        f"Suburb: {suburb}\n"
        f"AI Score: {score}/100"
    )
    await send_telegram_alert(message)


async def send_agent_status(agent_name: str, status: str, details: Optional[str] = None):
    """Send agent run status update"""
    message = f"AGENT STATUS\n{agent_name}: {status}"
    if details:
        message += f"\n{details}"
    await send_telegram_alert(message)


async def send_system_error(error: str, component: str):
    """Send critical system error alert"""
    message = f"SYSTEM ERROR\nComponent: {component}\nError: {error}\nACTION REQUIRED"
    await send_telegram_alert(message)
