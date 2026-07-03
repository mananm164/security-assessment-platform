from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from apps.audit.models import AuditLog
from apps.audit.services import record_audit_event
from apps.tenancy.selectors import can_write_client_records

from .selectors import visible_findings_for
from .serializers import FindingSerializer


class FindingViewSet(viewsets.ModelViewSet):
    serializer_class = FindingSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        queryset = visible_findings_for(self.request.user)
        assessment_id = self.request.query_params.get("assessment")
        if assessment_id:
            queryset = queryset.filter(assessment_id=assessment_id)
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        severity = self.request.query_params.get("severity")
        if severity:
            queryset = queryset.filter(severity=severity)
        return queryset

    def perform_create(self, serializer):
        assessment = serializer.validated_data["assessment"]
        if not can_write_client_records(self.request.user, assessment.client):
            raise PermissionDenied("You cannot create findings for this assessment.")
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        finding = serializer.instance
        assessment = serializer.validated_data.get("assessment", finding.assessment)
        if not can_write_client_records(self.request.user, assessment.client):
            raise PermissionDenied("You cannot update findings for this assessment.")
        tracked_fields = ["status", "remediation_owner", "due_date", "business_impact", "remediation"]
        before = {field: getattr(finding, field) for field in tracked_fields}
        updated = serializer.save()
        changed_fields = [field for field in tracked_fields if before[field] != getattr(updated, field)]
        if changed_fields:
            record_audit_event(
                actor=self.request.user,
                client=updated.assessment.client,
                assessment=updated.assessment,
                action=AuditLog.Action.FINDING_UPDATED,
                entity_type="Finding",
                entity_id=updated.id,
                summary=f"Finding updated: {', '.join(changed_fields)}.",
                metadata={
                    "changed_fields": changed_fields,
                    "status": updated.status,
                    "remediation_owner": updated.remediation_owner,
                    "due_date": updated.due_date.isoformat() if updated.due_date else None,
                },
            )
