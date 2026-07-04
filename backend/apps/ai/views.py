from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.findings.selectors import visible_findings_for
from apps.tenancy.selectors import can_write_client_records
from .models import AIArtifact
from .selectors import visible_ai_artifacts_for
from .serializers import AIArtifactSerializer
from .services.remediation_service import RemediationService


class FindingAIArtifactsView(APIView):
    permission_classes = [IsAuthenticated]

    def get_finding(self, request, finding_id):
        finding = visible_findings_for(request.user).filter(id=finding_id).first()
        if finding is None:
            raise NotFound("Finding not found.")
        return finding

    def get(self, request, finding_id):
        finding = self.get_finding(request, finding_id)
        artifacts = visible_ai_artifacts_for(request.user).filter(
            finding=finding, artifact_type=AIArtifact.ArtifactType.REMEDIATION
        )
        serializer = AIArtifactSerializer(artifacts, many=True)
        return Response({"items": serializer.data})


class GenerateRemediationView(FindingAIArtifactsView):
    def post(self, request, finding_id):
        finding = self.get_finding(request, finding_id)
        if not can_write_client_records(request.user, finding.assessment.client):
            raise PermissionDenied("You cannot generate remediation drafts for this finding.")
        artifact = RemediationService().generate(finding=finding, actor=request.user)
        return Response(AIArtifactSerializer(artifact).data, status=status.HTTP_201_CREATED)
