from __future__ import annotations

from django.db.models import Count, Q
from django.utils import timezone

from apps.accounts.models import User
from apps.audit.selectors import visible_audit_logs_for
from apps.findings.models import Finding
from apps.findings.selectors import visible_findings_for
from apps.imports.models import FindingSource
from apps.imports.selectors import visible_imports_for

NON_ACTIVE_STATUSES = [Finding.Status.CLOSED, Finding.Status.ACCEPTED_RISK]
INTERNAL_ROLES = {User.Role.ADMIN, User.Role.CONSULTANT, User.Role.MANAGER}


def _distribution(rows, key_name: str, count_name: str = "count") -> list[dict]:
    return [{key_name: row[key_name], "count": row[count_name]} for row in rows]


def dashboard_summary_for(user) -> dict:
    findings = visible_findings_for(user)
    imports = visible_imports_for(user)
    today = timezone.localdate()
    active_findings = findings.exclude(status__in=NON_ACTIVE_STATUSES)
    internal = bool(user and user.is_authenticated and user.role in INTERNAL_ROLES)

    severity_rows = findings.values("severity").annotate(count=Count("id")).order_by("severity")
    status_rows = findings.values("status").annotate(count=Count("id")).order_by("status")
    source_rows = (
        FindingSource.objects.filter(finding__in=findings)
        .values("scanner_observation__source_tool")
        .annotate(finding_count=Count("finding_id", distinct=True))
        .order_by("scanner_observation__source_tool")
    )
    recent_imports = list(imports.order_by("-created_at")[:5]) if internal else []
    top_priority = list(
        findings.order_by("-priority_score", "-cvss_score", "-updated_at")[:5]
    )
    recent_activity = list(visible_audit_logs_for(user).order_by("-created_at")[:8]) if internal else []

    response = {
        "metrics": {
            "open_findings": active_findings.count(),
            "critical_high_findings": findings.filter(
                severity__in=[Finding.Severity.CRITICAL, Finding.Severity.HIGH]
            ).exclude(status=Finding.Status.CLOSED).count(),
            "overdue_remediations": active_findings.filter(due_date__lt=today).count(),
            "recent_imports": len(recent_imports),
        },
        "severity_distribution": _distribution(severity_rows, "severity"),
        "status_distribution": _distribution(status_rows, "status"),
        "source_distribution": [
            {
                "source_tool": row["scanner_observation__source_tool"] or "MANUAL",
                "finding_count": row["finding_count"],
            }
            for row in source_rows
        ],
        "top_priority_findings": [
            {
                "id": finding.id,
                "title": finding.title,
                "severity": finding.severity,
                "priority_score": finding.priority_score,
                "priority_label": finding.priority_label,
                "status": finding.status,
                "due_date": finding.due_date,
            }
            for finding in top_priority
        ],
    }
    if internal:
        response["recent_imports"] = [
            {
                "id": item.id,
                "assessment": item.assessment_id,
                "source_tool": item.source_tool,
                "source_filename": item.source_filename,
                "status": item.status,
                "observations_created": item.observations_created,
                "observations_updated": item.observations_updated,
                "created_at": item.created_at,
            }
            for item in recent_imports
        ]
        response["recent_activity"] = [
            {
                "id": log.id,
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "summary": log.summary,
                "actor": {"id": log.actor_id, "email": log.actor.email} if log.actor_id else None,
                "safe_metadata": log.safe_metadata or log.metadata,
                "created_at": log.created_at,
            }
            for log in recent_activity
        ]
    else:
        response["metrics"].pop("recent_imports", None)

    # Temporary backward-compatible keys for older callers/tests while React moves to the Day 10 shape.
    response["open_findings"] = response["metrics"]["open_findings"]
    response["critical_high_findings"] = response["metrics"]["critical_high_findings"]
    response["overdue_remediation"] = response["metrics"]["overdue_remediations"]
    response["findings_by_severity"] = {row["severity"]: row["count"] for row in response["severity_distribution"]}
    response["findings_by_scanner_source"] = {row["source_tool"]: row["finding_count"] for row in response["source_distribution"]}
    if not internal:
        response["recent_imports"] = []
    return response
