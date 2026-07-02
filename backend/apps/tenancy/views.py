from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from .models import Client
from .selectors import can_manage_clients, visible_clients_for
from .serializers import ClientSerializer


class ClientViewSet(viewsets.ModelViewSet):
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        return visible_clients_for(self.request.user)

    def perform_create(self, serializer):
        if not can_manage_clients(self.request.user):
            raise PermissionDenied("Only administrators can create clients.")
        serializer.save()

    def perform_update(self, serializer):
        if not can_manage_clients(self.request.user):
            raise PermissionDenied("Only administrators can update clients.")
        serializer.save()
