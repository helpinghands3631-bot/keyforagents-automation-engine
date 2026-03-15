"""
KeyforAgents.com - Master FastAPI Gateway
Orchestrates all AI agents, handles webhooks, manages auth and routing
Endpoints: /api/webhooks/stripe, /api/leads, /api/agents, /api/health
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

# Internal imports
from billing.stripe_webhook import app as stripe_app
from integrations.notion_crm import add_lead_to_notion, create_task_in_notion
from integrations.telegram_notify import send_telegram_alert, send_agent_status

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_SECRET_KEY = os.getenv("API_SECRET_KEY", "keyforagents-secret")
security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != API_SECRET_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return credentials.credentials


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("KeyforAgents Automation Engine starting...")
    await send_telegram_alert("KeyforAgents Engine ONLINE - All systems go!")
    yield
    logger.info("KeyforAgents Automation Engine shutting down...")


app = FastAPI(
    title="KeyforAgents Automation Engine",
    description="Master API gateway for KeyforAgents.com AI automation system",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://keyforagents.com", "https://www.keyforagents.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Stripe webhook handler
app.mount("/stripe", stripe_app)


# --- Models ---
class LeadRequest(BaseModel):
    name: str
    email: str
    agency: str
    suburb: str
    score: Optional[int] = 50
    source: Optional[str] = "Apollo"


class AgentRunRequest(BaseModel):
    agent_name: str
    task: str
    params: Optional[dict] = {}


# --- Health Check ---
@app.get("/api/health")
async def health_check():
    return {
        "status": "online",
        "service": "KeyforAgents Automation Engine",
        "version": "1.0.0",
        "environment": os.getenv("ENV", "production")
    }


# --- Lead Endpoints ---
@app.post("/api/leads", dependencies=[Depends(verify_token)])
async def create_lead(lead: LeadRequest):
    """Add a new lead to Notion CRM and send Telegram alert"""
    notion_id = await add_lead_to_notion(lead.dict())
    if notion_id:
        await send_telegram_alert(
            f"NEW LEAD\n{lead.name} @ {lead.agency}\nSuburb: {lead.suburb}\nScore: {lead.score}/100"
        )
        return {"status": "created", "notion_id": notion_id, "lead": lead.name}
    raise HTTPException(status_code=500, detail="Failed to create lead in Notion")


@app.get("/api/leads/stats", dependencies=[Depends(verify_token)])
async def lead_stats():
    """Get lead pipeline statistics"""
    return {
        "message": "Lead stats endpoint - connect to Databricks for live data",
        "docs": "/docs"
    }


# --- Agent Endpoints ---
@app.post("/api/agents/run", dependencies=[Depends(verify_token)])
async def run_agent(request: AgentRunRequest):
    """Trigger an AI agent task"""
    await send_agent_status(request.agent_name, "STARTED", f"Task: {request.task}")
    await create_task_in_notion(
        task_title=f"Agent Run: {request.agent_name}",
        description=f"Task: {request.task}\nParams: {request.params}",
        priority="High"
    )
    return {
        "status": "triggered",
        "agent": request.agent_name,
        "task": request.task
    }


@app.get("/api/agents/status", dependencies=[Depends(verify_token)])
async def agents_status():
    """Get all active agent statuses"""
    return {
        "agents": [
            {"name": "lead_agent", "status": "active"},
            {"name": "sales_agent", "status": "active"},
            {"name": "telegram_agent", "status": "active"},
            {"name": "databricks_connector", "status": "active"}
        ]
    }


# --- Revenue Endpoints ---
@app.get("/api/revenue/summary", dependencies=[Depends(verify_token)])
async def revenue_summary():
    """Get revenue summary from Stripe + Databricks"""
    return {
        "message": "Connect Stripe + Databricks for live revenue data",
        "stripe_dashboard": "https://dashboard.stripe.com",
        "account": "acct_1SGCdzAgFztlVK66"
    }


if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
