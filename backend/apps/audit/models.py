from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    class Action(models.TextChoices):
        SCAN_IMPORT_CREATED = "SCAN_IMPORT_CREATED", "Scan import created"
        IMPORT_PREVIEW_CREATED = "IMPORT_PREVIEW_CREATED", "Import preview created"
        IMPORT_CONFIRMED = "IMPORT_CONFIRMED", "Import confirmed"
        OBSERVATION_TRIAGED = "OBSERVATION_TRIAGED", "Observation triaged"
        OBSERVATION_PROMOTED = "OBSERVATION_PROMOTED", "Observation promoted"
        FINDING_CREATED = "FINDING_CREATED", "Finding created"
        FINDING_UPDATED = "FINDING_UPDATED", "Finding updated"
        FINDING_STATUS_CHANGED = "FINDING_STATUS_CHANGED", "Finding status changed"
        FINDING_OWNER_CHANGED = "FINDING_OWNER_CHANGED", "Finding owner changed"
        FINDING_DUE_DATE_CHANGED = "FINDING_DUE_DATE_CHANGED", "Finding due date changed"
        FINDING_RISK_ACCEPTED = "FINDING_RISK_ACCEPTED", "Finding risk accepted"
        FINDING_REOPENED = "FINDING_REOPENED", "Finding reopened"
        FINDING_CLOSED = "FINDING_CLOSED", "Finding closed"
        INTELLIGENCE_REFRESHED = "INTELLIGENCE_REFRESHED", "Intelligence refreshed"
        AI_REMEDIATION_DRAFT_GENERATED = "AI_REMEDIATION_DRAFT_GENERATED", "AI remediation draft generated"
        # Legacy Day 8 value retained so old rows remain readable.
        IMPORT_CREATED = "IMPORT_CREATED", "Import created"

    client = models.ForeignKey("tenancy.Client", on_delete=models.CASCADE, related_name="audit_logs")
    assessment = models.ForeignKey(
        "assessments.Assessment",
        on_delete=models.CASCADE,
        related_name="audit_logs",
        null=True,
        blank=True,
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=80, choices=Action.choices)
    entity_type = models.CharField(max_length=80)
    entity_id = models.PositiveBigIntegerField()
    summary = models.CharField(max_length=255)
    metadata = models.JSONField(default=dict, blank=True)
    safe_metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["client", "-created_at"]),
            models.Index(fields=["assessment", "-created_at"]),
            models.Index(fields=["entity_type", "entity_id", "-created_at"]),
            models.Index(fields=["client", "entity_type", "entity_id", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.action} {self.entity_type}#{self.entity_id}"
