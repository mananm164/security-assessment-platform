from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from apps.tenancy.selectors import can_write_client_records

from .selectors import visible_assets_for, visible_assessments_for
from .serializers import AssetSerializer, AssessmentSerializer


class AssessmentViewSet(viewsets.ModelViewSet):
    serializer_class = AssessmentSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        queryset = visible_assessments_for(self.request.user)
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        client_id = self.request.query_params.get("client")
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        return queryset

    def perform_create(self, serializer):
        client = serializer.validated_data["client"]
        if not can_write_client_records(self.request.user, client):
            raise PermissionDenied("You cannot create assessments for this client.")
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        client = serializer.validated_data.get("client", serializer.instance.client)
        if not can_write_client_records(self.request.user, client):
            raise PermissionDenied("You cannot update assessments for this client.")
        serializer.save()


class AssetViewSet(viewsets.ModelViewSet):
    serializer_class = AssetSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        queryset = visible_assets_for(self.request.user)
        assessment_id = self.request.query_params.get("assessment")
        if assessment_id:
            queryset = queryset.filter(assessment_id=assessment_id)
        return queryset

    def perform_create(self, serializer):
        assessment = serializer.validated_data["assessment"]
        if not can_write_client_records(self.request.user, assessment.client):
            raise PermissionDenied("You cannot create assets for this assessment.")
        serializer.save()

    def perform_update(self, serializer):
        assessment = serializer.validated_data.get("assessment", serializer.instance.assessment)
        if not can_write_client_records(self.request.user, assessment.client):
            raise PermissionDenied("You cannot update assets for this assessment.")
        serializer.save()
