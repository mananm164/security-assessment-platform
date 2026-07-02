from rest_framework.routers import DefaultRouter

from .views import AssetViewSet, AssessmentViewSet

router = DefaultRouter()
router.register("assessments", AssessmentViewSet, basename="assessment")
router.register("assets", AssetViewSet, basename="asset")

urlpatterns = router.urls
