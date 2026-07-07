from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AssessmentImportPreviewCreateView, ImportPreviewViewSet, ScanImportViewSet, ScannerObservationViewSet

router = DefaultRouter()
router.register("imports", ScanImportViewSet, basename="scanimport")
router.register("observations", ScannerObservationViewSet, basename="scannerobservation")
router.register("import-previews", ImportPreviewViewSet, basename="importpreview")

urlpatterns = [
    path(
        "assessments/<int:assessment_id>/import-previews/",
        AssessmentImportPreviewCreateView.as_view(),
        name="assessment-import-preview-list",
    ),
] + router.urls
