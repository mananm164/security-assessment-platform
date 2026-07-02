from django.shortcuts import get_object_or_404

from rest_framework import decorators, response, status, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.findings.serializers import FindingSerializer

from .models import ScanImport
from .selectors import visible_imports_for, visible_observations_for
from .serializers import (
    ObservationPromotionSerializer,
    ObservationTriageSerializer,
    ScanImportSerializer,
    ScannerObservationSerializer,
)
from .services.promotion_service import promote_observation_to_finding
from .services.triage_service import triage_observation


class ScanImportViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ScanImportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = visible_imports_for(self.request.user)
        source_tool = self.request.query_params.get("source_tool")
        if source_tool:
            queryset = queryset.filter(source_tool=source_tool.upper())
        return queryset

    @decorators.action(detail=True, methods=["get"])
    def observations(self, request, pk=None):
        scan_import = self.get_object()
        queryset = visible_observations_for(request.user).filter(import_links__scan_import=scan_import)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ScannerObservationSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ScannerObservationSerializer(queryset, many=True)
        return response.Response(serializer.data)


class ScannerObservationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ScannerObservationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = visible_observations_for(self.request.user)
        assessment_id = self.request.query_params.get("assessment")
        if assessment_id:
            queryset = queryset.filter(assessment_id=assessment_id)
        source_tool = self.request.query_params.get("source_tool")
        if source_tool:
            queryset = queryset.filter(source_tool=source_tool.upper())
        return queryset

    @decorators.action(detail=True, methods=["post"])
    def triage(self, request, pk=None):
        observation = self.get_object()
        serializer = ObservationTriageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        duplicate_of = None
        duplicate_of_id = serializer.validated_data.get("duplicate_of_id")
        if duplicate_of_id is not None:
            duplicate_of = get_object_or_404(visible_observations_for(request.user), id=duplicate_of_id)
        observation = triage_observation(
            observation=observation,
            actor=request.user,
            triage_status=serializer.validated_data["triage_status"],
            triage_note=serializer.validated_data.get("triage_note", ""),
            duplicate_of=duplicate_of,
        )
        return response.Response(ScannerObservationSerializer(observation).data)

    @decorators.action(detail=True, methods=["post"])
    def promote(self, request, pk=None):
        observation = self.get_object()
        serializer = ObservationPromotionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        finding = promote_observation_to_finding(
            observation=observation,
            actor=request.user,
            **serializer.validated_data,
        )
        return response.Response(FindingSerializer(finding).data, status=status.HTTP_201_CREATED)
