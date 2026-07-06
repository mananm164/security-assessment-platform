from rest_framework.response import Response
from rest_framework.views import APIView

from .services.dashboard_service import dashboard_summary_for


class DashboardSummaryView(APIView):
    def get(self, request):
        return Response(dashboard_summary_for(request.user))
