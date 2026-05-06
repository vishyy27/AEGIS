"""
Phase 11.8: Fleet Intelligence Service.
Multi-service fleet-wide intelligence and service risk profiling.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case

from ..models.deployment import Deployment
from ..models.alerts import Alert
from ..models.phase11_models import ServiceProfile

logger = logging.getLogger("aegis.fleet")


class FleetIntelligence:
    def get_fleet_overview(self, db: Session) -> Dict[str, Any]:
        """Get fleet-wide overview with aggregated metrics."""
        total = db.query(func.count(Deployment.id)).scalar() or 0
        avg_risk = db.query(func.avg(Deployment.risk_score)).scalar() or 0
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent = db.query(func.count(Deployment.id)).filter(Deployment.timestamp >= seven_days_ago).scalar() or 0
        blocked = db.query(func.count(Deployment.id)).filter(Deployment.deployment_decision == "BLOCK").scalar() or 0

        services = db.query(Deployment.repo_name).distinct().count()

        return {
            "total_deployments": total,
            "total_services": services,
            "avg_risk_score": round(float(avg_risk), 2),
            "deployments_7d": recent,
            "blocked_total": blocked,
            "block_rate": round(blocked / total * 100, 1) if total > 0 else 0,
        }

    def get_service_profiles(self, db: Session) -> List[Dict[str, Any]]:
        """Get risk profiles for all tracked services."""
        services = (
            db.query(
                Deployment.repo_name,
                func.count(Deployment.id).label("total"),
                func.avg(Deployment.risk_score).label("avg_risk"),
                func.max(Deployment.risk_score).label("max_risk"),
                func.max(Deployment.timestamp).label("last_deploy"),
            )
            .filter(Deployment.repo_name.isnot(None))
            .group_by(Deployment.repo_name)
            .all()
        )

        profiles = []
        for s in services:
            # Calculate failure rate
            failures = (
                db.query(func.count(Deployment.id))
                .filter(
                    Deployment.repo_name == s.repo_name,
                    Deployment.deployment_outcome.in_(["failure", "error", "rollback", "failed"]),
                )
                .scalar() or 0
            )
            failure_rate = round(failures / s.total, 4) if s.total > 0 else 0

            # Stability score (inverse of volatility)
            avg_risk = float(s.avg_risk or 0)
            stability = max(0, round(100 - avg_risk - (failure_rate * 50), 1))

            # Risk trend (compare last 3 vs previous 3)
            recent_3 = (
                db.query(func.avg(Deployment.risk_score))
                .filter(Deployment.repo_name == s.repo_name)
                .order_by(desc(Deployment.timestamp))
                .limit(3)
                .scalar() or 0
            )
            trend = "stable"
            if float(recent_3) > avg_risk + 10:
                trend = "degrading"
            elif float(recent_3) < avg_risk - 10:
                trend = "improving"

            health = "healthy"
            if avg_risk > 70 or failure_rate > 0.3:
                health = "critical"
            elif avg_risk > 50 or failure_rate > 0.15:
                health = "warning"

            profiles.append({
                "service": s.repo_name,
                "total_deployments": s.total,
                "avg_risk": round(avg_risk, 2),
                "max_risk": float(s.max_risk or 0),
                "failure_rate": failure_rate,
                "stability_score": stability,
                "risk_trend": trend,
                "health_status": health,
                "last_deployment": s.last_deploy.isoformat() if s.last_deploy else None,
            })

        return sorted(profiles, key=lambda p: p["stability_score"])

    def get_risk_heatmap(self, db: Session, days: int = 7) -> List[Dict[str, Any]]:
        """Generate risk heatmap data for fleet visualization."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        deployments = (
            db.query(Deployment)
            .filter(Deployment.timestamp >= cutoff)
            .order_by(Deployment.timestamp.asc())
            .all()
        )

        heatmap = []
        for d in deployments:
            if d.repo_name and d.risk_score is not None:
                heatmap.append({
                    "service": d.repo_name,
                    "risk_score": d.risk_score,
                    "decision": d.deployment_decision,
                    "timestamp": d.timestamp.isoformat() if d.timestamp else None,
                    "day": d.timestamp.strftime("%a") if d.timestamp else None,
                    "hour": d.timestamp.hour if d.timestamp else 0,
                })

        return heatmap

    def get_service_ranking(self, db: Session, sort_by: str = "risk") -> List[Dict[str, Any]]:
        """Rank services by risk, stability, or deployment volume."""
        profiles = self.get_service_profiles(db)
        if sort_by == "stability":
            return sorted(profiles, key=lambda p: p["stability_score"])
        elif sort_by == "deployments":
            return sorted(profiles, key=lambda p: p["total_deployments"], reverse=True)
        return sorted(profiles, key=lambda p: p["avg_risk"], reverse=True)


fleet_intelligence = FleetIntelligence()
