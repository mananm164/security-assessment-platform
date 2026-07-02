from rest_framework import serializers

from .models import Client


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ("id", "name", "industry", "contact_name", "contact_email", "created_at")
        read_only_fields = ("id", "created_at")
