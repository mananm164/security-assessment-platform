from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.findings.models import Finding
from apps.findings.selectors import visible_findings_for
from apps.imports.models import FindingSource, ScanImport
from apps.imports.selectors import visible_imports_for

OPEN_STATUSES = [Finding.Status.OPEN, Finding.Status.IN_PROGRESS]


class DashboardSummaryView(APIView):
    def get(self, request):
        findings = visible_findings_for(request.user)
        imports = visible_imports_for(request.user)
        today = timezone.localdate()

        open_findings = findings.filter(status__in=OPEN_STATUSES)
        severity_rows = findings.values("severity").annotate(count=Count("id")).order_by("severity")
        source_rows = (
            FindingSource.objects.filter(finding__in=findings)
            .values("scanner_observation__source_tool")
            .annotate(count=Count("finding_id", distinct=True))
            .order_by("scanner_observation__source_tool")
        )
        recent_imports = imports.order_by("-created_at")[:5]

        return Response(
            {
                "open_findings": open_findings.count(),
                "critical_high_findings": findings.filter(
                    severity__in=[Finding.Severity.CRITICAL, Finding.Severity.HIGH],
                    status__in=OPEN_STATUSES,
                ).count(),
                "overdue_remediation": findings.filter(status__in=OPEN_STATUSES, due_date__lt=today).count(),
                "findings_by_severity": {row["severity"]: row["count"] for row in severity_rows},
                "findings_by_scanner_source": {
                    row["scanner_observation__source_tool"] or "MANUAL": row["count"] for row in source_rows
                },
                "recent_imports": [
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
                ],
            }
        )
