from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.tenancy.selectors import can_write_client_records, user_is_admin
from .selectors import visible_finding_for_intelligence
from .serializers import FindingIntelligenceSerializer
from .services.intelligence_service import IntelligenceService


class FindingIntelligenceView(APIView):
    permission_classes = [IsAuthenticated]

    def get_finding(self, request, finding_id):
        finding = visible_finding_for_intelligence(request.user, finding_id)
        if finding is None:
            raise NotFound("Finding not found.")
        return finding

    def get(self, request, finding_id):
        finding = self.get_finding(request, finding_id)
        intel = IntelligenceService.get_for_finding(finding) if finding.cve_id else None
        serializer = FindingIntelligenceSerializer({"finding": finding, "intelligence": intel, "used_cache": False})
        return Response(serializer.data)


class RefreshFindingIntelligenceView(FindingIntelligenceView):
    def post(self, request, finding_id):
        finding = self.get_finding(request, finding_id)
        if not can_write_client_records(request.user, finding.assessment.client):
            raise PermissionDenied("You cannot refresh intelligence for this finding.")
        force = bool(request.data.get("force", False))
        if force and not user_is_admin(request.user):
            raise PermissionDenied("Only administrators can force refresh intelligence.")
        result = IntelligenceService().refresh_for_finding(finding, force=force)
        finding.refresh_from_db()
        serializer = FindingIntelligenceSerializer({"finding": finding, "intelligence": result.intel, "used_cache": result.used_cache})
        return Response(serializer.data, status=status.HTTP_200_OK)
