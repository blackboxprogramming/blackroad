"""
Admin Dashboard API
Provides revenue metrics, user analytics, and system health endpoints.
All endpoints require ADMIN_TOKEN authentication.
"""

from fastapi import FastAPI, HTTPException, Depends, Header, Query
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import os
from sqlalchemy import text, func
from database import SessionLocal, engine
from models import StripeCustomer, MonthlyUsage, UserTier, Charge, Invoice

app = FastAPI(title="BlackRoad Admin Dashboard", version="1.0.0")

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "dev-admin-token-change-in-prod")

def verify_admin_token(authorization: Optional[str] = Header(None)) -> str:
    """Verify admin token from Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = authorization.replace("Bearer ", "")
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid admin token")
    
    return token


# ============================================================================
# REVENUE METRICS ENDPOINTS
# ============================================================================

@app.get("/api/admin/revenue/total")
async def get_total_revenue(
    _: str = Depends(verify_admin_token),
    days: Optional[int] = Query(30, ge=1, le=365),
):
    """Get total revenue over last N days"""
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        result = db.query(
            func.sum(Charge.amount_usd).label("total_revenue"),
            func.count(Charge.id).label("total_charges"),
            func.avg(Charge.amount_usd).label("avg_charge"),
        ).filter(
            Charge.created_at >= cutoff_date,
            Charge.status == "completed"
        ).first()
        
        return {
            "period_days": days,
            "start_date": cutoff_date.isoformat(),
            "end_date": datetime.utcnow().isoformat(),
            "total_revenue_usd": float(result[0] or 0),
            "total_charges": result[1] or 0,
            "avg_charge_usd": float(result[2] or 0),
        }
    finally:
        db.close()


@app.get("/api/admin/revenue/by-tier")
async def get_revenue_by_tier(
    _: str = Depends(verify_admin_token),
    days: Optional[int] = Query(30, ge=1, le=365),
):
    """Get revenue breakdown by user tier"""
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        results = db.query(
            UserTier.tier,
            func.count(Charge.id).label("charge_count"),
            func.sum(Charge.amount_usd).label("tier_revenue"),
            func.avg(Charge.amount_usd).label("avg_charge"),
        ).join(
            StripeCustomer,
            UserTier.customer_id == StripeCustomer.customer_id
        ).join(
            Charge,
            StripeCustomer.customer_id == Charge.customer_id
        ).filter(
            Charge.created_at >= cutoff_date,
            Charge.status == "completed"
        ).group_by(
            UserTier.tier
        ).order_by(
            func.sum(Charge.amount_usd).desc()
        ).all()
        
        return {
            "period_days": days,
            "by_tier": [
                {
                    "tier": tier,
                    "charge_count": count,
                    "total_revenue_usd": float(revenue or 0),
                    "avg_charge_usd": float(avg_charge or 0),
                }
                for tier, count, revenue, avg_charge in results
            ]
        }
    finally:
        db.close()


@app.get("/api/admin/revenue/daily")
async def get_daily_revenue(
    _: str = Depends(verify_admin_token),
    days: Optional[int] = Query(30, ge=1, le=365),
):
    """Get daily revenue trend"""
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        results = db.query(
            func.date(Charge.created_at).label("date"),
            func.sum(Charge.amount_usd).label("daily_revenue"),
            func.count(Charge.id).label("daily_charges"),
        ).filter(
            Charge.created_at >= cutoff_date,
            Charge.status == "completed"
        ).group_by(
            func.date(Charge.created_at)
        ).order_by(
            func.date(Charge.created_at).asc()
        ).all()
        
        return {
            "period_days": days,
            "daily_trend": [
                {
                    "date": date.isoformat(),
                    "revenue_usd": float(revenue or 0),
                    "charge_count": count,
                }
                for date, revenue, count in results
            ]
        }
    finally:
        db.close()


@app.get("/api/admin/revenue/projection")
async def get_revenue_projection(
    _: str = Depends(verify_admin_token),
    days_history: Optional[int] = Query(30, ge=7, le=365),
):
    """Project annual revenue based on last N days"""
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_history)
        
        result = db.query(
            func.sum(Charge.amount_usd).label("recent_revenue"),
            func.count(Charge.id).label("recent_charges"),
        ).filter(
            Charge.created_at >= cutoff_date,
            Charge.status == "completed"
        ).first()
        
        if not result[0]:
            return {
                "annual_projection_usd": 0,
                "based_on_days": days_history,
                "note": "Insufficient data"
            }
        
        daily_avg = float(result[0]) / days_history
        annual_projection = daily_avg * 365
        
        return {
            "annual_projection_usd": annual_projection,
            "daily_average_usd": daily_avg,
            "recent_period_revenue_usd": float(result[0]),
            "based_on_days": days_history,
            "charge_count": result[1],
        }
    finally:
        db.close()


# ============================================================================
# USER ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/api/admin/users/total")
async def get_total_users(
    _: str = Depends(verify_admin_token),
):
    """Get total active users by tier"""
    db = SessionLocal()
    try:
        results = db.query(
            UserTier.tier,
            func.count(UserTier.customer_id).label("user_count"),
            func.avg(MonthlyUsage.current_month_usage).label("avg_usage"),
            func.max(MonthlyUsage.current_month_usage).label("max_usage"),
        ).outerjoin(
            MonthlyUsage,
            UserTier.customer_id == MonthlyUsage.customer_id
        ).group_by(
            UserTier.tier
        ).order_by(
            func.count(UserTier.customer_id).desc()
        ).all()
        
        total_users = sum(count for _, count, _, _ in results)
        
        return {
            "total_users": total_users,
            "by_tier": [
                {
                    "tier": tier,
                    "user_count": count,
                    "avg_monthly_usage": avg_usage or 0,
                    "max_monthly_usage": max_usage or 0,
                }
                for tier, count, avg_usage, max_usage in results
            ]
        }
    finally:
        db.close()


@app.get("/api/admin/users/growth")
async def get_user_growth(
    _: str = Depends(verify_admin_token),
    days: Optional[int] = Query(30, ge=1, le=365),
):
    """Get daily user signup trend"""
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        results = db.query(
            func.date(StripeCustomer.created_at).label("date"),
            func.count(StripeCustomer.customer_id).label("daily_signups"),
        ).filter(
            StripeCustomer.created_at >= cutoff_date
        ).group_by(
            func.date(StripeCustomer.created_at)
        ).order_by(
            func.date(StripeCustomer.created_at).asc()
        ).all()
        
        return {
            "period_days": days,
            "daily_signups": [
                {
                    "date": date.isoformat(),
                    "signups": count,
                }
                for date, count in results
            ]
        }
    finally:
        db.close()


@app.get("/api/admin/users/churn")
async def get_user_churn(
    _: str = Depends(verify_admin_token),
    days: Optional[int] = Query(30, ge=1, le=365),
):
    """Calculate churn rate (canceled subscriptions)"""
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Total users who had an active subscription at start of period
        start_active = db.query(func.count(UserTier.customer_id)).filter(
            UserTier.created_at < cutoff_date,
            UserTier.tier != "free",
        ).scalar() or 0
        
        # Users who canceled during period
        canceled = db.query(func.count(UserTier.customer_id)).filter(
            UserTier.updated_at >= cutoff_date,
            UserTier.tier == "free",  # Assume canceled = downgrade to free
        ).scalar() or 0
        
        churn_rate = (canceled / start_active * 100) if start_active > 0 else 0
        
        return {
            "period_days": days,
            "start_active_paid_users": start_active,
            "canceled_users": canceled,
            "churn_rate_percent": churn_rate,
        }
    finally:
        db.close()


@app.get("/api/admin/users/paid-conversion")
async def get_paid_conversion(
    _: str = Depends(verify_admin_token),
):
    """Get percentage of users who have paid"""
    db = SessionLocal()
    try:
        total_users = db.query(func.count(UserTier.customer_id)).scalar() or 0
        paid_users = db.query(func.count(UserTier.customer_id)).filter(
            UserTier.tier != "free"
        ).scalar() or 0
        
        conversion_rate = (paid_users / total_users * 100) if total_users > 0 else 0
        
        return {
            "total_users": total_users,
            "paid_users": paid_users,
            "free_users": total_users - paid_users,
            "paid_conversion_rate_percent": conversion_rate,
        }
    finally:
        db.close()


# ============================================================================
# SYSTEM HEALTH ENDPOINTS
# ============================================================================

@app.get("/api/admin/health/database")
async def get_database_health(
    _: str = Depends(verify_admin_token),
):
    """Check database connectivity and performance"""
    db = SessionLocal()
    try:
        start = datetime.utcnow()
        
        # Simple query to test connectivity
        db.execute(text("SELECT 1"))
        
        latency_ms = (datetime.utcnow() - start).total_seconds() * 1000
        
        # Get table sizes
        result = db.execute(text("""
            SELECT
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
            FROM pg_tables
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        """)).fetchall()
        
        return {
            "status": "healthy",
            "connectivity_latency_ms": latency_ms,
            "tables": [
                {"schema": row[0], "table": row[1], "size": row[2]}
                for row in result
            ]
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
    finally:
        db.close()


@app.get("/api/admin/health/pending-invoices")
async def get_pending_invoices(
    _: str = Depends(verify_admin_token),
):
    """Get number of pending/failed invoices"""
    db = SessionLocal()
    try:
        pending = db.query(func.count(Invoice.id)).filter(
            Invoice.status == "pending"
        ).scalar() or 0
        
        failed = db.query(func.count(Invoice.id)).filter(
            Invoice.status == "failed"
        ).scalar() or 0
        
        return {
            "pending_invoices": pending,
            "failed_invoices": failed,
            "total_issues": pending + failed,
        }
    finally:
        db.close()


@app.get("/api/admin/health/failed-charges")
async def get_failed_charges(
    _: str = Depends(verify_admin_token),
    hours: Optional[int] = Query(24, ge=1, le=720),
):
    """Get recent failed charges"""
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        results = db.query(
            Charge.id,
            Charge.customer_id,
            Charge.amount_usd,
            Charge.created_at,
        ).filter(
            Charge.status == "failed",
            Charge.created_at >= cutoff
        ).order_by(
            Charge.created_at.desc()
        ).all()
        
        return {
            "time_window_hours": hours,
            "failed_charge_count": len(results),
            "recent_failures": [
                {
                    "charge_id": r[0],
                    "customer_id": r[1],
                    "amount_usd": float(r[2]),
                    "timestamp": r[3].isoformat(),
                }
                for r in results[:20]  # Limit to 20 most recent
            ]
        }
    finally:
        db.close()


# ============================================================================
# TIER MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/api/admin/tiers/distribution")
async def get_tier_distribution(
    _: str = Depends(verify_admin_token),
):
    """Get distribution of users across tiers"""
    db = SessionLocal()
    try:
        results = db.query(
            UserTier.tier,
            func.count(UserTier.customer_id).label("user_count"),
            func.sum(Charge.amount_usd).label("total_revenue"),
        ).outerjoin(
            Charge,
            UserTier.customer_id == Charge.customer_id
        ).group_by(
            UserTier.tier
        ).all()
        
        total_users = sum(count for _, count, _ in results)
        
        return {
            "total_users": total_users,
            "tier_breakdown": [
                {
                    "tier": tier,
                    "user_count": count,
                    "percentage": (count / total_users * 100) if total_users > 0 else 0,
                    "total_revenue_usd": float(revenue or 0),
                }
                for tier, count, revenue in results
            ]
        }
    finally:
        db.close()


@app.get("/api/admin/tiers/mrr")
async def get_monthly_recurring_revenue(
    _: str = Depends(verify_admin_token),
):
    """Get MRR by tier (assumes monthly subscriptions)"""
    db = SessionLocal()
    try:
        # Tier pricing (adjust as needed)
        tier_pricing = {
            "free": 0,
            "light": 25,
            "power": 225,
            "enterprise": 975,
        }
        
        results = db.query(
            UserTier.tier,
            func.count(UserTier.customer_id).label("user_count"),
        ).filter(
            UserTier.tier != "free"
        ).group_by(
            UserTier.tier
        ).all()
        
        mrr_by_tier = [
            {
                "tier": tier,
                "user_count": count,
                "monthly_per_user_usd": tier_pricing.get(tier, 0),
                "tier_mrr_usd": count * tier_pricing.get(tier, 0),
            }
            for tier, count in results
        ]
        
        total_mrr = sum(item["tier_mrr_usd"] for item in mrr_by_tier)
        
        return {
            "monthly_recurring_revenue_usd": total_mrr,
            "annual_run_rate_usd": total_mrr * 12,
            "by_tier": mrr_by_tier
        }
    finally:
        db.close()


# ============================================================================
# INVOICE ENDPOINTS
# ============================================================================

@app.get("/api/admin/invoices/summary")
async def get_invoice_summary(
    _: str = Depends(verify_admin_token),
):
    """Get summary of all invoices"""
    db = SessionLocal()
    try:
        results = db.query(
            Invoice.status,
            func.count(Invoice.id).label("count"),
            func.sum(Invoice.total_usd).label("total_revenue"),
        ).group_by(
            Invoice.status
        ).all()
        
        return {
            "by_status": [
                {
                    "status": status,
                    "invoice_count": count,
                    "total_revenue_usd": float(revenue or 0),
                }
                for status, count, revenue in results
            ]
        }
    finally:
        db.close()


@app.get("/api/admin/invoices/overdue")
async def get_overdue_invoices(
    _: str = Depends(verify_admin_token),
    days_overdue: Optional[int] = Query(30, ge=1),
):
    """Get invoices overdue by N days"""
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=days_overdue)
        
        results = db.query(
            Invoice.id,
            Invoice.customer_id,
            Invoice.total_usd,
            Invoice.due_date,
        ).filter(
            Invoice.status == "unpaid",
            Invoice.due_date < cutoff
        ).order_by(
            Invoice.due_date.asc()
        ).all()
        
        return {
            "overdue_threshold_days": days_overdue,
            "overdue_invoice_count": len(results),
            "total_overdue_usd": sum(r[2] for r in results),
            "recent_overdue": [
                {
                    "invoice_id": r[0],
                    "customer_id": r[1],
                    "amount_usd": float(r[2]),
                    "due_date": r[3].isoformat(),
                }
                for r in results[:20]
            ]
        }
    finally:
        db.close()


# ============================================================================
# EXPORT ENDPOINTS
# ============================================================================

@app.get("/api/admin/export/daily-report")
async def export_daily_report(
    _: str = Depends(verify_admin_token),
):
    """Get comprehensive daily report"""
    db = SessionLocal()
    try:
        today = datetime.utcnow().date()
        
        daily_revenue = db.query(
            func.sum(Charge.amount_usd).label("total")
        ).filter(
            func.date(Charge.created_at) == today,
            Charge.status == "completed"
        ).scalar() or 0
        
        daily_signups = db.query(
            func.count(StripeCustomer.customer_id).label("total")
        ).filter(
            func.date(StripeCustomer.created_at) == today
        ).scalar() or 0
        
        total_users = db.query(func.count(UserTier.customer_id)).scalar() or 0
        paid_users = db.query(func.count(UserTier.customer_id)).filter(
            UserTier.tier != "free"
        ).scalar() or 0
        
        return {
            "date": today.isoformat(),
            "generated_at": datetime.utcnow().isoformat(),
            "daily_metrics": {
                "revenue_usd": float(daily_revenue),
                "new_signups": daily_signups,
            },
            "user_metrics": {
                "total_users": total_users,
                "paid_users": paid_users,
                "free_users": total_users - paid_users,
            },
        }
    finally:
        db.close()


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/api/admin/ping")
async def ping(_: str = Depends(verify_admin_token)):
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
