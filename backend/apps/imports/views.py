from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.urls import reverse

from rest_framework import decorators, response, status, views, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.assessments.models import Assessment
from apps.common.exceptions import ImportValidationError
from apps.findings.serializers import FindingSerializer
from apps.tenancy.selectors import visible_clients_for

from .models import ImportPreview
from .selectors import visible_imports_for, visible_observations_for
from .serializers import (
    ImportPreviewConfirmSerializer,
    ImportPreviewSerializer,
    ObservationPromotionSerializer,
    ObservationTriageSerializer,
    ScanImportSerializer,
    ScannerObservationSerializer,
)
from .services.preview_service import (
    ImportPreviewExpired,
    confirm_import_preview,
    create_import_preview,
    get_visible_preview,
)
from .services.promotion_service import promote_observation_to_finding
from .services.triage_service import triage_observation


def _safe_bad_request(exc):
    return response.Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


def _permission_denied(exc):
    return response.Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)


def _expired_response():
    return response.Response(
        {"detail": "This import preview has expired. Upload the report again to continue."},
        status=status.HTTP_410_GONE,
    )


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


class AssessmentImportPreviewCreateView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, assessment_id):
        assessment = get_object_or_404(
            Assessment.objects.select_related("client").filter(client__in=visible_clients_for(request.user)),
            id=assessment_id,
        )
        source_tool = request.data.get("source_tool")
        upload = request.FILES.get("report_file")
        if not source_tool or upload is None:
            return response.Response(
                {"detail": "Select a source tool and report file."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            preview = create_import_preview(
                actor=request.user,
                assessment=assessment,
                source_tool=source_tool,
                upload=upload,
            )
        except PermissionDenied as exc:
            return _permission_denied(exc)
        except ImportValidationError as exc:
            return _safe_bad_request(exc)
        return response.Response(ImportPreviewSerializer(preview).data, status=status.HTTP_201_CREATED)


class ImportPreviewViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, pk=None):
        try:
            preview = get_visible_preview(actor=request.user, preview_id=pk)
        except ImportPreview.DoesNotExist:
            return response.Response(status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as exc:
            return _permission_denied(exc)
        except ImportPreviewExpired:
            return _expired_response()
        return response.Response(ImportPreviewSerializer(preview).data)

    @decorators.action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        try:
            preview = get_visible_preview(actor=request.user, preview_id=pk)
            already_confirmed = bool(preview.confirmed_at and preview.scan_import_id)
            result = confirm_import_preview(actor=request.user, preview=preview)
        except ImportPreview.DoesNotExist:
            return response.Response(status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as exc:
            return _permission_denied(exc)
        except ImportPreviewExpired:
            return _expired_response()
        payload = {
            "scan_import_id": result.scan_import.id,
            "assessment": result.scan_import.assessment_id,
            "source_tool": result.scan_import.source_tool,
            "observations_created": result.observations_created,
            "observations_reobserved": result.observations_reobserved,
            "detail_url": reverse("scanimport-detail", args=[result.scan_import.id]),
        }
        serializer = ImportPreviewConfirmSerializer(payload)
        return response.Response(
            serializer.data,
            status=status.HTTP_200_OK if already_confirmed else status.HTTP_201_CREATED,
        )


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
