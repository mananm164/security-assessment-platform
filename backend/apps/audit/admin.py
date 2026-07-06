from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "entity_type", "entity_id", "client", "actor", "created_at")
    list_filter = ("action", "entity_type", "created_at")
    search_fields = ("entity_type", "entity_id", "summary")
    readonly_fields = ("created_at",)
