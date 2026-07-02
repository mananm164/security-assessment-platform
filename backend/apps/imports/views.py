from rest_framework import decorators, response, viewsets
from rest_framework.permissions import IsAuthenticated

from .models import ScanImport
from .selectors import visible_imports_for, visible_observations_for
from .serializers import ScanImportSerializer, ScannerObservationSerializer


class ScanImportViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ScanImportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return visible_imports_for(self.request.user)

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
        return queryset
