"""
Customer Analytics Dashboard API
Provides per-customer analytics, usage patterns, and revenue insights
"""

from fastapi import FastAPI, HTTPException, Depends, Header, Query
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import os
from sqlalchemy import text, func
from database import SessionLocal, engine
from models import StripeCustomer, MonthlyUsage, UserTier, Charge, Invoice

app = FastAPI(title="BlackRoad Customer Analytics", version="1.0.0")

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
# CUSTOMER LIST & OVERVIEW
# ============================================================================

@app.get("/api/analytics/customers")
async def list_customers(
    _: str = Depends(verify_admin_token),
    limit: Optional[int] = Query(100, ge=1, le=1000),
    offset: Optional[int] = Query(0, ge=0),
    tier: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("created_at", regex="^(created_at|revenue|usage)$"),
):
    """List all customers with summary stats"""
    db = SessionLocal()
    try:
        query = db.query(
            StripeCustomer.customer_id,
            StripeCustomer.stripe_id,
            StripeCustomer.created_at,
            UserTier.tier,
            func.count(Charge.id).label("charge_count"),
            func.sum(Charge.amount_usd).label("total_revenue"),
            func.avg(Charge.amount_usd).label("avg_charge"),
            func.coalesce(MonthlyUsage.current_month_usage, 0).label("current_usage"),
        ).join(
            UserTier,
            StripeCustomer.customer_id == UserTier.customer_id,
            isouter=True
        ).join(
            MonthlyUsage,
            StripeCustomer.customer_id == MonthlyUsage.customer_id,
            isouter=True
        ).join(
            Charge,
            StripeCustomer.customer_id == Charge.customer_id,
            isouter=True
        ).group_by(
            StripeCustomer.customer_id,
            StripeCustomer.stripe_id,
            StripeCustomer.created_at,
            UserTier.tier,
            MonthlyUsage.current_month_usage
        )
        
        if tier:
            query = query.filter(UserTier.tier == tier)
        
        # Sort options
        if sort_by == "revenue":
            query = query.order_by(func.sum(Charge.amount_usd).desc())
        elif sort_by == "usage":
            query = query.order_by(func.coalesce(MonthlyUsage.current_month_usage, 0).desc())
        else:
            query = query.order_by(StripeCustomer.created_at.desc())
        
        total_count = query.count()
        results = query.limit(limit).offset(offset).all()
        
        return {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "customers": [
                {
                    "customer_id": r[0],
                    "stripe_id": r[1],
                    "created_at": r[2].isoformat(),
                    "tier": r[3] or "free",
                    "charge_count": r[4] or 0,
                    "total_revenue_usd": float(r[5] or 0),
                    "avg_charge_usd": float(r[6] or 0),
                    "current_month_usage": r[7] or 0,
                }
                for r in results
            ]
        }
    finally:
        db.close()


@app.get("/api/analytics/customer/{customer_id}/profile")
async def get_customer_profile(
    customer_id: str,
    _: str = Depends(verify_admin_token),
):
    """Get detailed customer profile"""
    db = SessionLocal()
    try:
        customer = db.query(StripeCustomer).filter(
            StripeCustomer.customer_id == customer_id
        ).first()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        tier = db.query(UserTier).filter(
            UserTier.customer_id == customer_id
        ).first()
        
        # Calculate metrics
        total_charges = db.query(func.count(Charge.id)).filter(
            Charge.customer_id == customer_id
        ).scalar() or 0
        
        total_revenue = db.query(func.sum(Charge.amount_usd)).filter(
            Charge.customer_id == customer_id,
            Charge.status == "completed"
        ).scalar() or 0
        
        usage = db.query(MonthlyUsage).filter(
            MonthlyUsage.customer_id == customer_id
        ).order_by(MonthlyUsage.year_month.desc()).first()
        
        return {
            "customer_id": customer.customer_id,
            "stripe_id": customer.stripe_id,
            "created_at": customer.created_at.isoformat(),
            "updated_at": customer.updated_at.isoformat(),
            "tier": tier.tier if tier else "free",
            "tier_updated_at": tier.updated_at.isoformat() if tier else None,
            "metrics": {
                "total_charges": total_charges,
                "total_revenue_usd": float(total_revenue),
                "current_month_usage": usage.current_month_usage if usage else 0,
                "monthly_limit": usage.monthly_limit_requests if usage else 5 * 3600 * 7200,
            }
        }
    finally:
        db.close()


# ============================================================================
# CUSTOMER REVENUE & USAGE
# ============================================================================

@app.get("/api/analytics/customer/{customer_id}/revenue")
async def get_customer_revenue(
    customer_id: str,
    _: str = Depends(verify_admin_token),
    days: Optional[int] = Query(90, ge=1, le=365),
):
    """Get customer revenue history"""
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Verify customer exists
        customer = db.query(StripeCustomer).filter(
            StripeCustomer.customer_id == customer_id
        ).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        charges = db.query(
            func.date(Charge.created_at).label("date"),
            func.sum(Charge.amount_usd).label("daily_revenue"),
            func.count(Charge.id).label("charge_count"),
        ).filter(
            Charge.customer_id == customer_id,
            Charge.created_at >= cutoff,
            Charge.status == "completed"
        ).group_by(
            func.date(Charge.created_at)
        ).order_by(
            func.date(Charge.created_at).asc()
        ).all()
        
        total_revenue = sum(r[1] for r in charges)
        
        return {
            "customer_id": customer_id,
            "period_days": days,
            "total_revenue_usd": float(total_revenue),
            "daily_breakdown": [
                {
                    "date": date.isoformat(),
                    "revenue_usd": float(revenue),
                    "charge_count": count,
                }
                for date, revenue, count in charges
            ]
        }
    finally:
        db.close()


@app.get("/api/analytics/customer/{customer_id}/usage")
async def get_customer_usage(
    customer_id: str,
    _: str = Depends(verify_admin_token),
):
    """Get customer usage for current month"""
    db = SessionLocal()
    try:
        usage = db.query(MonthlyUsage).filter(
            MonthlyUsage.customer_id == customer_id
        ).order_by(
            MonthlyUsage.year_month.desc()
        ).first()
        
        if not usage:
            return {
                "customer_id": customer_id,
                "current_month_usage": 0,
                "monthly_limit_requests": 5 * 3600 * 7200,
                "usage_percent": 0,
                "remaining": 5 * 3600 * 7200,
                "status": "active"
            }
        
        usage_percent = (usage.current_month_usage / usage.monthly_limit_requests * 100) if usage.monthly_limit_requests > 0 else 0
        remaining = max(0, usage.monthly_limit_requests - usage.current_month_usage)
        
        # Determine status
        if usage_percent >= 100:
            status = "exceeded"
        elif usage_percent >= 90:
            status = "near_limit"
        else:
            status = "active"
        
        return {
            "customer_id": customer_id,
            "year_month": usage.year_month,
            "current_month_usage": usage.current_month_usage,
            "monthly_limit_requests": usage.monthly_limit_requests,
            "soft_limit_requests": usage.soft_limit_requests,
            "hard_limit_requests": usage.hard_limit_requests,
            "usage_percent": usage_percent,
            "remaining": remaining,
            "status": status,
            "reset_date": usage.reset_date.isoformat() if usage.reset_date else None,
        }
    finally:
        db.close()


# ============================================================================
# CUSTOMER BEHAVIOR & TRENDS
# ============================================================================

@app.get("/api/analytics/customer/{customer_id}/trend")
async def get_customer_trend(
    customer_id: str,
    _: str = Depends(verify_admin_token),
    metric: Optional[str] = Query("revenue", regex="^(revenue|usage|charges)$"),
):
    """Get customer trend data"""
    db = SessionLocal()
    try:
        if metric == "revenue":
            # Revenue trend
            results = db.query(
                func.date_trunc('week', Charge.created_at).label("week"),
                func.sum(Charge.amount_usd).label("revenue"),
            ).filter(
                Charge.customer_id == customer_id,
                Charge.status == "completed",
                Charge.created_at >= datetime.utcnow() - timedelta(days=90)
            ).group_by(
                func.date_trunc('week', Charge.created_at)
            ).order_by(
                func.date_trunc('week', Charge.created_at)
            ).all()
            
            return {
                "customer_id": customer_id,
                "metric": "revenue",
                "trend": [
                    {
                        "period": str(week),
                        "value": float(revenue or 0),
                    }
                    for week, revenue in results
                ]
            }
        
        elif metric == "usage":
            # Usage trend
            results = db.query(
                MonthlyUsage.year_month,
                MonthlyUsage.current_month_usage,
            ).filter(
                MonthlyUsage.customer_id == customer_id
            ).order_by(
                MonthlyUsage.year_month.desc()
            ).limit(12).all()
            
            return {
                "customer_id": customer_id,
                "metric": "usage",
                "trend": [
                    {
                        "month": month,
                        "usage": usage,
                    }
                    for month, usage in reversed(results)
                ]
            }
        
        else:  # charges
            results = db.query(
                func.date_trunc('week', Charge.created_at).label("week"),
                func.count(Charge.id).label("charge_count"),
            ).filter(
                Charge.customer_id == customer_id,
                Charge.created_at >= datetime.utcnow() - timedelta(days=90)
            ).group_by(
                func.date_trunc('week', Charge.created_at)
            ).order_by(
                func.date_trunc('week', Charge.created_at)
            ).all()
            
            return {
                "customer_id": customer_id,
                "metric": "charges",
                "trend": [
                    {
                        "period": str(week),
                        "count": count,
                    }
                    for week, count in results
                ]
            }
    finally:
        db.close()


# ============================================================================
# CUSTOMER COHORT ANALYSIS
# ============================================================================

@app.get("/api/analytics/cohorts")
async def get_cohorts(
    _: str = Depends(verify_admin_token),
):
    """Get customer cohorts by signup period"""
    db = SessionLocal()
    try:
        cohorts = db.query(
            func.date_trunc('month', StripeCustomer.created_at).label("cohort_month"),
            func.count(StripeCustomer.customer_id).label("cohort_size"),
            func.avg(func.coalesce(
                func.sum(Charge.amount_usd), 0
            )).label("avg_revenue_per_user"),
        ).outerjoin(
            Charge,
            StripeCustomer.customer_id == Charge.customer_id
        ).group_by(
            func.date_trunc('month', StripeCustomer.created_at)
        ).order_by(
            func.date_trunc('month', StripeCustomer.created_at).desc()
        ).all()
        
        return {
            "cohorts": [
                {
                    "cohort_month": str(month),
                    "cohort_size": size,
                    "avg_revenue_per_user": float(revenue or 0),
                }
                for month, size, revenue in cohorts
            ]
        }
    finally:
        db.close()


@app.get("/api/analytics/cohort/{cohort_month}/retention")
async def get_cohort_retention(
    cohort_month: str,  # Format: "2024-01"
    _: str = Depends(verify_admin_token),
):
    """Get retention rate for a cohort"""
    db = SessionLocal()
    try:
        # Parse cohort month
        try:
            cohort_date = datetime.strptime(cohort_month, "%Y-%m")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid cohort_month format (use YYYY-MM)")
        
        # Get all customers in cohort
        cohort_customers = db.query(StripeCustomer.customer_id).filter(
            func.date_trunc('month', StripeCustomer.created_at) == cohort_date
        ).all()
        
        cohort_ids = [c[0] for c in cohort_customers]
        cohort_size = len(cohort_ids)
        
        if cohort_size == 0:
            return {
                "cohort_month": cohort_month,
                "cohort_size": 0,
                "retention": []
            }
        
        # Check activity by month
        retention = []
        for month_offset in range(13):
            check_month = cohort_date + timedelta(days=30*month_offset)
            
            active = db.query(func.count(Charge.id)).filter(
                Charge.customer_id.in_(cohort_ids),
                func.date_trunc('month', Charge.created_at) == check_month
            ).scalar() or 0
            
            if active > 0:
                retention_rate = (active / cohort_size) * 100
                retention.append({
                    "month_offset": month_offset,
                    "active_customers": active,
                    "retention_rate": retention_rate,
                })
        
        return {
            "cohort_month": cohort_month,
            "cohort_size": cohort_size,
            "retention": retention
        }
    finally:
        db.close()


# ============================================================================
# CUSTOMER SEGMENTATION
# ============================================================================

@app.get("/api/analytics/segments")
async def get_customer_segments(
    _: str = Depends(verify_admin_token),
):
    """Get customer segments by behavior"""
    db = SessionLocal()
    try:
        # VIP: > $1000 total revenue
        vip = db.query(func.count(StripeCustomer.customer_id)).join(
            Charge,
            StripeCustomer.customer_id == Charge.customer_id
        ).group_by(
            StripeCustomer.customer_id
        ).having(
            func.sum(Charge.amount_usd) > 1000
        ).count()
        
        # Growing: Revenue increased last month vs month before
        growing = db.query(func.count(distinct(StripeCustomer.customer_id))).filter(
            # Simplified: just count power and enterprise tiers
            UserTier.tier.in_(["power", "enterprise"])
        ).scalar() or 0
        
        # At Risk: High churn signals
        at_risk = db.query(func.count(UserTier.customer_id)).filter(
            UserTier.tier == "free"
        ).scalar() or 0
        
        # Inactive: No charges in last 30 days
        active_customers = db.query(func.distinct(Charge.customer_id)).filter(
            Charge.created_at >= datetime.utcnow() - timedelta(days=30)
        ).all()
        active_ids = [c[0] for c in active_customers]
        
        total_customers = db.query(func.count(StripeCustomer.customer_id)).scalar() or 1
        
        inactive = total_customers - len(active_ids)
        
        return {
            "total_customers": total_customers,
            "segments": [
                {
                    "name": "VIP",
                    "description": "High value customers (> $1000 total revenue)",
                    "count": vip,
                    "percentage": (vip / total_customers * 100) if total_customers > 0 else 0,
                },
                {
                    "name": "Growing",
                    "description": "Power and Enterprise tier users",
                    "count": growing,
                    "percentage": (growing / total_customers * 100) if total_customers > 0 else 0,
                },
                {
                    "name": "At Risk",
                    "description": "Free tier users (high churn risk)",
                    "count": at_risk,
                    "percentage": (at_risk / total_customers * 100) if total_customers > 0 else 0,
                },
                {
                    "name": "Inactive",
                    "description": "No charges in last 30 days",
                    "count": inactive,
                    "percentage": (inactive / total_customers * 100) if total_customers > 0 else 0,
                },
            ]
        }
    finally:
        db.close()


# ============================================================================
# CHURN ANALYSIS
# ============================================================================

@app.get("/api/analytics/churn-risk")
async def get_churn_risk(
    _: str = Depends(verify_admin_token),
):
    """Identify customers at risk of churning"""
    db = SessionLocal()
    try:
        # Customers with recent tier downgrade (free = churned)
        churned_recently = db.query(
            UserTier.customer_id,
            UserTier.tier,
            UserTier.updated_at,
            func.sum(Charge.amount_usd).label("last_revenue"),
        ).join(
            Charge,
            UserTier.customer_id == Charge.customer_id,
            isouter=True
        ).filter(
            UserTier.tier == "free",
            UserTier.updated_at >= datetime.utcnow() - timedelta(days=30)
        ).group_by(
            UserTier.customer_id,
            UserTier.tier,
            UserTier.updated_at
        ).limit(20).all()
        
        return {
            "at_risk_count": len(churned_recently),
            "at_risk_customers": [
                {
                    "customer_id": r[0],
                    "current_tier": r[1],
                    "downgraded_at": r[2].isoformat(),
                    "last_revenue_usd": float(r[3] or 0),
                }
                for r in churned_recently
            ]
        }
    finally:
        db.close()


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/api/analytics/ping")
async def ping(_: str = Depends(verify_admin_token)):
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
