from rest_framework.routers import DefaultRouter

from .views import ScanImportViewSet, ScannerObservationViewSet

router = DefaultRouter()
router.register("imports", ScanImportViewSet, basename="scanimport")
router.register("observations", ScannerObservationViewSet, basename="scannerobservation")

urlpatterns = router.urls
