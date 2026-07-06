from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.audit.serializers import AuditLogSerializer
from apps.audit.selectors import visible_audit_logs_for
from apps.audit.services import record_audit_event
from apps.tenancy.selectors import can_write_client_records

from .selectors import visible_findings_for
from .serializers import FindingSerializer
from .services.finding_lifecycle_service import update_finding_lifecycle


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
        finding = serializer.save(created_by=self.request.user)
        record_audit_event(
            actor=self.request.user,
            client=finding.assessment.client,
            assessment=finding.assessment,
            action=AuditLog.Action.FINDING_CREATED,
            entity_type="FINDING",
            entity_id=finding.id,
            summary=f"Finding created: {finding.title}.",
            safe_metadata={"severity": finding.severity, "status": finding.status},
        )

    def perform_update(self, serializer):
        updated = update_finding_lifecycle(
            finding=serializer.instance,
            actor=self.request.user,
            changes=serializer.validated_data,
        )
        serializer.instance = updated

    @action(detail=True, methods=["get"], url_path="audit-logs")
    def audit_logs(self, request, pk=None):
        finding = self.get_object()
        if request.user.role == User.Role.CLIENT:
            raise PermissionDenied("Client users cannot view internal audit timelines.")
        logs = visible_audit_logs_for(request.user).filter(entity_type="FINDING", entity_id=finding.id)
        page = self.paginate_queryset(logs)
        if page is not None:
            serializer = AuditLogSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = AuditLogSerializer(logs, many=True)
        return Response(serializer.data)
