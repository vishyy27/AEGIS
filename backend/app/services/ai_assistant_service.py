"""
Phase 11.7: AI DevOps Assistant Service.
Conversational operational intelligence using REAL deployment data.
"""

import logging
import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from ..models.deployment import Deployment
from ..models.alerts import Alert
from ..models.phase11_models import (
    ChatSession, ChatMessage, AnomalyEvent, IncidentTimeline, ServiceProfile
)
from ..config import settings

logger = logging.getLogger("aegis.assistant")

# Intent patterns for query classification
INTENT_PATTERNS = {
    "deployment_blocked": [r"why.*block", r"blocked", r"deployment.*denied", r"can't deploy"],
    "ml_disagreement": [r"ml.*disagree", r"model.*conflict", r"prediction.*wrong", r"ml.*explain"],
    "unstable_services": [r"unstable", r"flaky", r"failing.*service", r"problematic"],
    "deployment_trends": [r"trend", r"pattern", r"over time", r"last.*week", r"history"],
    "incident_cause": [r"incident", r"root.*cause", r"what.*happened", r"outage"],
    "risky_modules": [r"risky.*module", r"dangerous.*file", r"sensitive", r"high.*risk.*component"],
    "confidence_drops": [r"confidence.*drop", r"low.*confidence", r"uncertain", r"reliability"],
    "service_health": [r"health", r"status", r"how.*is.*service", r"service.*doing"],
    "recent_deployments": [r"recent.*deploy", r"latest.*deploy", r"last.*deploy"],
    "system_overview": [r"overview", r"summary", r"dashboard", r"how.*system"],
}


class AIAssistantService:
    def _classify_intent(self, query: str) -> str:
        query_lower = query.lower().strip()
        for intent, patterns in INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return intent
        return "general"

    def _build_context(self, db: Session, intent: str, query: str) -> Dict[str, Any]:
        """Build rich context from real data based on intent."""
        context: Dict[str, Any] = {"intent": intent, "query": query}

        if intent in ("deployment_blocked", "recent_deployments", "deployment_trends"):
            recent = db.query(Deployment).order_by(desc(Deployment.timestamp)).limit(10).all()
            context["recent_deployments"] = [{
                "id": d.id, "service": d.repo_name, "risk_score": d.risk_score,
                "decision": d.deployment_decision, "risk_level": d.risk_level,
                "outcome": d.deployment_outcome, "ml_prob": d.ml_prediction_prob,
                "confidence": d.policy_confidence_score,
                "timestamp": d.timestamp.isoformat() if d.timestamp else None,
            } for d in recent]

        if intent in ("unstable_services", "service_health"):
            # Aggregate service stats from deployments
            services = db.query(
                Deployment.repo_name,
                func.count(Deployment.id).label("total"),
                func.avg(Deployment.risk_score).label("avg_risk"),
                func.max(Deployment.risk_score).label("max_risk"),
            ).group_by(Deployment.repo_name).all()
            context["service_stats"] = [{
                "service": s.repo_name, "total_deployments": s.total,
                "avg_risk": round(float(s.avg_risk or 0), 2),
                "max_risk": float(s.max_risk or 0),
            } for s in services if s.repo_name]

        if intent in ("incident_cause",):
            incidents = db.query(IncidentTimeline).order_by(desc(IncidentTimeline.created_at)).limit(5).all()
            context["recent_incidents"] = [{
                "id": i.incident_id, "title": i.title,
                "severity": i.severity, "status": i.status,
                "root_cause": i.root_cause,
            } for i in incidents]

        if intent in ("confidence_drops", "ml_disagreement"):
            low_conf = db.query(Deployment).filter(Deployment.low_confidence_flag == True).order_by(desc(Deployment.timestamp)).limit(5).all()
            context["low_confidence_deployments"] = [{
                "id": d.id, "service": d.repo_name,
                "confidence": d.prediction_confidence_score,
                "ml_prob": d.ml_prediction_prob, "risk_score": d.risk_score,
            } for d in low_conf]

        if intent == "system_overview":
            total = db.query(func.count(Deployment.id)).scalar() or 0
            avg_risk = db.query(func.avg(Deployment.risk_score)).scalar() or 0
            blocked = db.query(func.count(Deployment.id)).filter(Deployment.deployment_decision == "BLOCK").scalar() or 0
            context["system_stats"] = {
                "total_deployments": total,
                "avg_risk_score": round(float(avg_risk), 2),
                "blocked_deployments": blocked,
            }

        return context

    def _generate_response(self, context: Dict[str, Any]) -> str:
        """Generate a contextual response based on real data."""
        intent = context["intent"]

        if intent == "deployment_blocked":
            deps = context.get("recent_deployments", [])
            blocked = [d for d in deps if d.get("decision") == "BLOCK"]
            if blocked:
                d = blocked[0]
                return (
                    f"🚫 **Deployment Blocked** — `{d['service']}` (ID: {d['id']})\n\n"
                    f"- **Risk Score**: {d['risk_score']}\n"
                    f"- **ML Failure Probability**: {(d.get('ml_prob') or 0)*100:.1f}%\n"
                    f"- **Confidence**: {(d.get('confidence') or 0)*100:.1f}%\n\n"
                    f"The policy engine blocked this deployment due to elevated risk indicators. "
                    f"Check the XAI waterfall in the deployment detail for a stage-by-stage breakdown."
                )
            return "No recently blocked deployments found. All recent deployments were permitted."

        if intent == "unstable_services":
            stats = context.get("service_stats", [])
            risky = sorted(stats, key=lambda s: s["avg_risk"], reverse=True)[:5]
            if not risky:
                return "No service data available yet. Deploy some services to start tracking stability."
            lines = ["📊 **Top Unstable Services** (by avg risk):\n"]
            for s in risky:
                emoji = "🔴" if s["avg_risk"] > 60 else "🟡" if s["avg_risk"] > 40 else "🟢"
                lines.append(f"{emoji} **{s['service']}** — Avg Risk: {s['avg_risk']}, Deployments: {s['total_deployments']}")
            return "\n".join(lines)

        if intent == "deployment_trends":
            deps = context.get("recent_deployments", [])
            if not deps:
                return "No deployment data available for trend analysis."
            scores = [d["risk_score"] for d in deps if d.get("risk_score") is not None]
            avg = sum(scores) / len(scores) if scores else 0
            trend = "📈 increasing" if len(scores) >= 2 and scores[0] > scores[-1] else "📉 decreasing"
            return (
                f"📊 **Deployment Trends** (last {len(deps)} deployments)\n\n"
                f"- **Average Risk Score**: {avg:.1f}\n"
                f"- **Risk Trend**: {trend}\n"
                f"- **Latest Risk**: {scores[0] if scores else 'N/A'}\n"
            )

        if intent == "incident_cause":
            incidents = context.get("recent_incidents", [])
            if not incidents:
                return "No incidents recorded. The system is operating normally."
            inc = incidents[0]
            return (
                f"🚨 **Latest Incident**: {inc['title']}\n\n"
                f"- **Severity**: {inc['severity']}\n"
                f"- **Status**: {inc['status']}\n"
                f"- **Root Cause**: {inc.get('root_cause') or 'Under investigation'}\n"
            )

        if intent == "confidence_drops":
            deps = context.get("low_confidence_deployments", [])
            if not deps:
                return "✅ No low-confidence predictions detected recently. ML model is performing well."
            lines = ["⚠️ **Low Confidence Deployments**:\n"]
            for d in deps:
                lines.append(f"- `{d['service']}` (ID: {d['id']}) — Confidence: {(d.get('confidence') or 0)*100:.1f}%")
            return "\n".join(lines)

        if intent == "system_overview":
            stats = context.get("system_stats", {})
            return (
                f"🏠 **AEGIS System Overview**\n\n"
                f"- **Total Deployments**: {stats.get('total_deployments', 0)}\n"
                f"- **Average Risk Score**: {stats.get('avg_risk_score', 0)}\n"
                f"- **Blocked Deployments**: {stats.get('blocked_deployments', 0)}\n"
            )

        return (
            "I can help you with deployment analysis. Try asking:\n"
            "- *Why was my deployment blocked?*\n"
            "- *Which services are unstable?*\n"
            "- *Show deployment trends*\n"
            "- *What caused the last incident?*\n"
            "- *System overview*"
        )

    def chat(self, db: Session, session_id: Optional[str], message: str) -> Dict[str, Any]:
        """Process a chat message and return AI response with context."""
        if not session_id:
            session_id = str(uuid.uuid4())

        # Get or create session
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session:
            session = ChatSession(session_id=session_id, title=message[:50])
            db.add(session)
            db.commit()

        # Save user message
        user_msg = ChatMessage(session_id=session_id, role="user", content=message)
        db.add(user_msg)

        # Process
        intent = self._classify_intent(message)
        context = self._build_context(db, intent, message)
        response_text = self._generate_response(context)

        # Save assistant message
        assistant_msg = ChatMessage(
            session_id=session_id, role="assistant",
            content=response_text, context_data=context,
            reasoning_chain={"intent": intent},
        )
        db.add(assistant_msg)
        db.commit()

        return {
            "session_id": session_id,
            "intent": intent,
            "response": response_text,
            "context_summary": {k: type(v).__name__ for k, v in context.items()},
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_sessions(self, db: Session, limit: int = 20) -> List[Dict[str, Any]]:
        sessions = db.query(ChatSession).order_by(desc(ChatSession.updated_at)).limit(limit).all()
        return [{
            "session_id": s.session_id, "title": s.title,
            "message_count": len(s.messages),
            "created_at": s.created_at.isoformat() if s.created_at else None,
        } for s in sessions]

    def get_session_messages(self, db: Session, session_id: str) -> List[Dict[str, Any]]:
        messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
        return [{
            "role": m.role, "content": m.content,
            "context_data": m.context_data,
            "timestamp": m.created_at.isoformat() if m.created_at else None,
        } for m in messages]


ai_assistant = AIAssistantService()
