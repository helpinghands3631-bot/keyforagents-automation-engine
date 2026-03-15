"""
Stripe Webhook Handler for KeyforAgents.com
Endpoint: https://keyforagents.com/api/webhooks/stripe
API Version: 2025-09-30.clover
Webhook: brilliant-excellence (Active)
Listening to: checkout.session.completed, customer.subscription.created,
               customer.subscription.updated, customer.subscription.deleted,
               invoice.payment_succeeded, invoice.payment_failed
"""

import os
import stripe
import logging
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from typing import Optional
from integrations.notion_crm import update_notion_on_payment
from integrations.telegram_notify import send_telegram_alert

logger = logging.getLogger(__name__)

STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")  # whsec_hXZrFpG07STr9WZwU8hisjqObHUiIPNQ
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

app = FastAPI()


@app.post("/api/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature")
):
    """Handle incoming Stripe webhook events for KeyforAgents.com"""
    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Stripe signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    event_type = event["type"]
    data = event["data"]["object"]

    logger.info(f"Received Stripe event: {event_type}")

    # --- Subscription Created ---
    if event_type == "customer.subscription.created":
        customer_id = data.get("customer")
        plan = data.get("items", {}).get("data", [{}])[0].get("price", {}).get("nickname", "Unknown")
        amount = data.get("items", {}).get("data", [{}])[0].get("price", {}).get("unit_amount", 0) / 100
        await handle_new_subscription(customer_id, plan, amount, data)

    # --- Checkout Completed ---
    elif event_type == "checkout.session.completed":
        customer_email = data.get("customer_details", {}).get("email", "")
        amount_total = data.get("amount_total", 0) / 100
        session_id = data.get("id", "")
        await handle_checkout_complete(customer_email, amount_total, session_id)

    # --- Payment Succeeded ---
    elif event_type == "invoice.payment_succeeded":
        customer_id = data.get("customer")
        amount_paid = data.get("amount_paid", 0) / 100
        invoice_id = data.get("id", "")
        await handle_payment_success(customer_id, amount_paid, invoice_id)

    # --- Payment Failed ---
    elif event_type == "invoice.payment_failed":
        customer_id = data.get("customer")
        amount = data.get("amount_due", 0) / 100
        await handle_payment_failed(customer_id, amount)

    # --- Subscription Updated ---
    elif event_type == "customer.subscription.updated":
        await handle_subscription_updated(data)

    # --- Subscription Deleted / Cancelled ---
    elif event_type == "customer.subscription.deleted":
        customer_id = data.get("customer")
        await handle_subscription_cancelled(customer_id)

    return JSONResponse({"status": "success", "event": event_type})


async def handle_new_subscription(customer_id: str, plan: str, amount: float, data: dict):
    """New subscription - update Notion CRM and alert via Telegram"""
    logger.info(f"New subscription: {customer_id} | Plan: {plan} | AUD${amount}")
    await update_notion_on_payment({
        "event": "subscription_created",
        "customer_id": customer_id,
        "plan": plan,
        "amount": amount,
        "status": "active"
    })
    await send_telegram_alert(
        f"NEW SUBSCRIPTION\nCustomer: {customer_id}\nPlan: {plan}\nAmount: AUD${amount}/mo"
    )


async def handle_checkout_complete(email: str, amount: float, session_id: str):
    """Checkout completed - notify and log"""
    logger.info(f"Checkout complete: {email} | AUD${amount}")
    await send_telegram_alert(
        f"CHECKOUT COMPLETE\nEmail: {email}\nAmount: AUD${amount}\nSession: {session_id}"
    )


async def handle_payment_success(customer_id: str, amount: float, invoice_id: str):
    """Successful payment - update CRM"""
    logger.info(f"Payment success: {customer_id} | AUD${amount}")
    await update_notion_on_payment({
        "event": "payment_success",
        "customer_id": customer_id,
        "amount": amount,
        "invoice_id": invoice_id
    })
    await send_telegram_alert(
        f"PAYMENT RECEIVED\nCustomer: {customer_id}\nAmount: AUD${amount}"
    )


async def handle_payment_failed(customer_id: str, amount: float):
    """Failed payment - urgent alert"""
    logger.warning(f"Payment FAILED: {customer_id} | AUD${amount}")
    await send_telegram_alert(
        f"PAYMENT FAILED\nCustomer: {customer_id}\nAmount: AUD${amount}\nACTION REQUIRED"
    )


async def handle_subscription_updated(data: dict):
    """Subscription plan changed"""
    customer_id = data.get("customer")
    status = data.get("status")
    logger.info(f"Subscription updated: {customer_id} | Status: {status}")


async def handle_subscription_cancelled(customer_id: str):
    """Subscription cancelled - churn alert"""
    logger.warning(f"Subscription CANCELLED: {customer_id}")
    await update_notion_on_payment({
        "event": "subscription_cancelled",
        "customer_id": customer_id,
        "status": "cancelled"
    })
    await send_telegram_alert(
        f"SUBSCRIPTION CANCELLED\nCustomer: {customer_id}\nFollow up ASAP!"
    )
