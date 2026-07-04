from django.urls import path

from .views import FindingIntelligenceView, RefreshFindingIntelligenceView

urlpatterns = [
    path("findings/<int:finding_id>/intelligence/", FindingIntelligenceView.as_view(), name="finding-intelligence"),
    path("findings/<int:finding_id>/intelligence/refresh/", RefreshFindingIntelligenceView.as_view(), name="finding-intelligence-refresh"),
]
