from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Assessment(models.Model):
    class Framework(models.TextChoices):
        ISO_27001 = "ISO_27001", "ISO 27001"
        NIST = "NIST", "NIST"
        OWASP = "OWASP", "OWASP"
        NIS2 = "NIS2", "NIS2"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        PLANNED = "PLANNED", "Planned"
        ACTIVE = "ACTIVE", "Active"
        COMPLETED = "COMPLETED", "Completed"
        ARCHIVED = "ARCHIVED", "Archived"

    client = models.ForeignKey(
        "tenancy.Client",
        on_delete=models.CASCADE,
        related_name="assessments",
    )
    name = models.CharField(max_length=255)
    framework = models.CharField(max_length=20, choices=Framework.choices)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNED,
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    scope_summary = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_assessments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "name"]

    def clean(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date cannot be before start date."})

    def __str__(self) -> str:
        return f"{self.client}: {self.name}"


class Asset(models.Model):
    class AssetType(models.TextChoices):
        HOST = "HOST", "Host"
        APPLICATION = "APPLICATION", "Application"
        API = "API", "API"
        DATABASE = "DATABASE", "Database"
        CLOUD_RESOURCE = "CLOUD_RESOURCE", "Cloud resource"
        OTHER = "OTHER", "Other"

    class Environment(models.TextChoices):
        DEVELOPMENT = "DEVELOPMENT", "Development"
        TEST = "TEST", "Test"
        STAGING = "STAGING", "Staging"
        PRODUCTION = "PRODUCTION", "Production"
        UNKNOWN = "UNKNOWN", "Unknown"

    class Criticality(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"

    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name="assets",
    )
    asset_type = models.CharField(max_length=20, choices=AssetType.choices)
    display_name = models.CharField(max_length=255, blank=True)
    hostname = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    base_url = models.URLField(blank=True)
    environment = models.CharField(
        max_length=20,
        choices=Environment.choices,
        default=Environment.UNKNOWN,
    )
    criticality = models.CharField(max_length=20, choices=Criticality.choices)
    internet_exposed = models.BooleanField(default=False)
    owner = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["assessment__name", "display_name", "hostname", "base_url"]

    def clean(self):
        if not any([self.display_name, self.hostname, self.ip_address, self.base_url]):
            raise ValidationError(
                "Asset must have at least one identifier: display name, hostname, IP address or base URL."
            )

    def __str__(self) -> str:
        return self.display_name or self.hostname or self.base_url or str(self.ip_address)
