from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

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
        assessment = serializer.validated_data.get("assessment", serializer.instance.assessment)
        if not can_write_client_records(self.request.user, assessment.client):
            raise PermissionDenied("You cannot update findings for this assessment.")
        serializer.save()
