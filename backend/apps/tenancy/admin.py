from django.contrib import admin

from .models import Client, ClientMembership


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "industry", "contact_email", "created_at")
    search_fields = ("name", "industry", "contact_name", "contact_email")


@admin.register(ClientMembership)
class ClientMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "client", "relationship_role", "is_active", "created_at")
    list_filter = ("relationship_role", "is_active")
    search_fields = ("user__email", "client__name")
