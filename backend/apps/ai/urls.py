from django.urls import path

from .views import FindingAIArtifactsView, GenerateRemediationView

urlpatterns = [
    path("findings/<int:finding_id>/ai-artifacts/", FindingAIArtifactsView.as_view(), name="finding-ai-artifacts"),
    path("findings/<int:finding_id>/ai/remediation/", GenerateRemediationView.as_view(), name="finding-ai-remediation"),
]
