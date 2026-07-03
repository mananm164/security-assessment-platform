from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    class Action(models.TextChoices):
        IMPORT_CREATED = "IMPORT_CREATED", "Import created"
        OBSERVATION_TRIAGED = "OBSERVATION_TRIAGED", "Observation triaged"
        OBSERVATION_PROMOTED = "OBSERVATION_PROMOTED", "Observation promoted"
        FINDING_UPDATED = "FINDING_UPDATED", "Finding updated"

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
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["client", "-created_at"]),
            models.Index(fields=["assessment", "-created_at"]),
            models.Index(fields=["entity_type", "entity_id", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.action} {self.entity_type}#{self.entity_id}"
