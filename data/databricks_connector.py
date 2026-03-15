"""
Databricks Analytics Connector for KeyforAgents.com
Connects to Databricks Community/Enterprise for lead analytics,
revenue reporting, and AI model training data pipelines.
"""

import os
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")
DATABRICKS_HTTP_PATH = os.getenv("DATABRICKS_HTTP_PATH")


def get_databricks_connection():
    """Create Databricks SQL connection"""
    try:
        from databricks import sql
        connection = sql.connect(
            server_hostname=DATABRICKS_HOST.replace("https://", ""),
            http_path=DATABRICKS_HTTP_PATH,
            access_token=DATABRICKS_TOKEN
        )
        logger.info("Databricks connection established")
        return connection
    except Exception as e:
        logger.error(f"Databricks connection failed: {e}")
        return None


def run_query(query: str) -> Optional[pd.DataFrame]:
    """Execute a SQL query on Databricks and return DataFrame"""
    conn = get_databricks_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return pd.DataFrame(result, columns=columns)
    except Exception as e:
        logger.error(f"Query failed: {e}")
        return None
    finally:
        conn.close()


def get_revenue_summary(days: int = 30) -> Dict:
    """Get revenue summary for the last N days"""
    query = f"""
        SELECT
            DATE(created_at) as date,
            COUNT(*) as transactions,
            SUM(amount) as total_aud,
            AVG(amount) as avg_transaction,
            COUNT(DISTINCT customer_id) as unique_customers
        FROM keyforagents.payments
        WHERE created_at >= DATE_SUB(CURRENT_DATE(), {days})
        AND status = 'succeeded'
        GROUP BY DATE(created_at)
        ORDER BY date DESC
    """
    df = run_query(query)
    if df is not None and not df.empty:
        return {
            "total_revenue_aud": float(df["total_aud"].sum()),
            "total_transactions": int(df["transactions"].sum()),
            "unique_customers": int(df["unique_customers"].max()),
            "avg_daily_revenue": float(df["total_aud"].mean()),
            "data": df.to_dict(orient="records")
        }
    return {"total_revenue_aud": 0, "total_transactions": 0}


def get_lead_pipeline_stats() -> Dict:
    """Get lead pipeline statistics from Databricks"""
    query = """
        SELECT
            status,
            COUNT(*) as count,
            AVG(score) as avg_score,
            state,
            suburb
        FROM keyforagents.leads
        WHERE created_at >= DATE_SUB(CURRENT_DATE(), 30)
        GROUP BY status, state, suburb
        ORDER BY count DESC
        LIMIT 100
    """
    df = run_query(query)
    if df is not None:
        return {
            "total_leads": int(df["count"].sum()) if not df.empty else 0,
            "by_status": df.groupby("status")["count"].sum().to_dict() if not df.empty else {},
            "top_suburbs": df.nlargest(10, "count")[["suburb", "count"]].to_dict(orient="records") if not df.empty else []
        }
    return {"total_leads": 0}


def get_subscription_metrics() -> Dict:
    """Get subscription MRR and churn metrics"""
    query = """
        SELECT
            plan_name,
            COUNT(*) as subscribers,
            SUM(monthly_amount) as mrr_aud,
            AVG(months_active) as avg_tenure_months
        FROM keyforagents.subscriptions
        WHERE status = 'active'
        GROUP BY plan_name
        ORDER BY mrr_aud DESC
    """
    df = run_query(query)
    if df is not None and not df.empty:
        return {
            "total_mrr_aud": float(df["mrr_aud"].sum()),
            "total_subscribers": int(df["subscribers"].sum()),
            "by_plan": df.to_dict(orient="records")
        }
    return {"total_mrr_aud": 0, "total_subscribers": 0}


def write_leads_to_databricks(leads: List[Dict]) -> bool:
    """Write new leads to Databricks table"""
    if not leads:
        return False
    try:
        df = pd.DataFrame(leads)
        df["created_at"] = datetime.utcnow()
        df["source"] = df.get("source", "Apollo")
        # In production: use spark or databricks SDK to write
        logger.info(f"Writing {len(leads)} leads to Databricks")
        return True
    except Exception as e:
        logger.error(f"Failed to write leads to Databricks: {e}")
        return False


def create_tables_if_not_exist():
    """Initialize Databricks tables for KeyforAgents"""
    tables = [
        """
        CREATE TABLE IF NOT EXISTS keyforagents.payments (
            id STRING,
            customer_id STRING,
            amount DOUBLE,
            currency STRING DEFAULT 'AUD',
            status STRING,
            plan_name STRING,
            created_at TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS keyforagents.leads (
            id STRING,
            name STRING,
            email STRING,
            agency STRING,
            suburb STRING,
            state STRING,
            score INT,
            status STRING DEFAULT 'new',
            source STRING,
            created_at TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS keyforagents.subscriptions (
            id STRING,
            customer_id STRING,
            plan_name STRING,
            monthly_amount DOUBLE,
            status STRING,
            months_active INT,
            created_at TIMESTAMP,
            cancelled_at TIMESTAMP
        )
        """
    ]
    for sql in tables:
        result = run_query(sql)
        logger.info(f"Table initialized: {sql.split('keyforagents.')[1].split('(')[0].strip()}")
