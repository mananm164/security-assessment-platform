from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Finding(models.Model):
    class Severity(models.TextChoices):
        INFORMATIONAL = "INFORMATIONAL", "Informational"
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"

    class PriorityLabel(models.TextChoices):
        URGENT = "URGENT", "Urgent"
        HIGH = "HIGH", "High"
        MEDIUM = "MEDIUM", "Medium"
        LOW = "LOW", "Low"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        ACCEPTED_RISK = "ACCEPTED_RISK", "Accepted risk"
        MITIGATED = "MITIGATED", "Mitigated"
        VALIDATION_PENDING = "VALIDATION_PENDING", "Validation pending"
        CLOSED = "CLOSED", "Closed"

    assessment = models.ForeignKey(
        "assessments.Assessment",
        on_delete=models.CASCADE,
        related_name="findings",
    )
    affected_asset = models.ForeignKey(
        "assessments.Asset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="findings",
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    cve_id = models.CharField(max_length=40, blank=True)
    cvss_score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(Decimal("0.0")), MaxValueValidator(Decimal("10.0"))],
    )
    severity = models.CharField(max_length=20, choices=Severity.choices, editable=False)
    business_impact = models.TextField()
    remediation = models.TextField()
    remediation_owner = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    due_date = models.DateField(null=True, blank=True)
    priority_score = models.PositiveSmallIntegerField(null=True, blank=True)
    priority_label = models.CharField(max_length=20, choices=PriorityLabel.choices, null=True, blank=True)
    priority_explanation = models.JSONField(default=dict, blank=True)
    priority_reason = models.CharField(max_length=500, null=True, blank=True)
    priority_computed_at = models.DateTimeField(null=True, blank=True)
    validation_evidence = models.TextField(blank=True)
    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="validated_findings",
    )
    validated_at = models.DateTimeField(null=True, blank=True)
    risk_acceptance_reason = models.TextField(blank=True)
    risk_accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="risk_accepted_findings",
    )
    risk_accepted_at = models.DateTimeField(null=True, blank=True)
    risk_review_due_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_findings",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "title"]

    @classmethod
    def derive_severity(cls, cvss_score: Decimal) -> str:
        score = Decimal(str(cvss_score))
        if score == Decimal("0.0"):
            return cls.Severity.INFORMATIONAL
        if score <= Decimal("3.9"):
            return cls.Severity.LOW
        if score <= Decimal("6.9"):
            return cls.Severity.MEDIUM
        if score <= Decimal("8.9"):
            return cls.Severity.HIGH
        return cls.Severity.CRITICAL

    def save(self, *args, **kwargs):
        self.severity = self.derive_severity(self.cvss_score)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.title
