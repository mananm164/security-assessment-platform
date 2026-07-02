from django.conf import settings
from django.db import models


class ScanImport(models.Model):
    class SourceTool(models.TextChoices):
        NMAP = "NMAP", "Nmap"
        ZAP = "ZAP", "OWASP ZAP"
        NESSUS = "NESSUS", "Nessus"
        BURP = "BURP", "Burp Suite"

    class Status(models.TextChoices):
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    assessment = models.ForeignKey(
        "assessments.Assessment",
        on_delete=models.CASCADE,
        related_name="scan_imports",
    )
    source_tool = models.CharField(max_length=20, choices=SourceTool.choices)
    source_filename = models.CharField(max_length=255)
    file_sha256 = models.CharField(max_length=64)
    imported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="scan_imports",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PROCESSING)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    observations_created = models.PositiveIntegerField(default=0)
    observations_updated = models.PositiveIntegerField(default=0)
    error_summary = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.source_tool} import {self.id} for assessment {self.assessment_id}"


class ScannerObservation(models.Model):
    class TriageStatus(models.TextChoices):
        NEW = "NEW", "New"
        CONFIRMED = "CONFIRMED", "Confirmed"
        FALSE_POSITIVE = "FALSE_POSITIVE", "False positive"
        DUPLICATE = "DUPLICATE", "Duplicate"
        ACCEPTED_RISK = "ACCEPTED_RISK", "Accepted risk"
        PROMOTED = "PROMOTED", "Promoted"

    assessment = models.ForeignKey(
        "assessments.Assessment",
        on_delete=models.CASCADE,
        related_name="scanner_observations",
    )
    asset = models.ForeignKey(
        "assessments.Asset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scanner_observations",
    )
    source_tool = models.CharField(max_length=20, choices=ScanImport.SourceTool.choices)
    external_id = models.CharField(max_length=255)
    scanner_plugin_id = models.CharField(max_length=255, blank=True)
    fingerprint = models.CharField(max_length=64)
    triage_status = models.CharField(
        max_length=20,
        choices=TriageStatus.choices,
        default=TriageStatus.NEW,
    )
    triage_note = models.CharField(max_length=1000, blank=True)
    triaged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="triaged_observations",
    )
    triaged_at = models.DateTimeField(null=True, blank=True)
    duplicate_of = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="duplicates",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    evidence_summary = models.TextField(blank=True)
    raw_severity = models.CharField(max_length=80, blank=True)
    confidence = models.CharField(max_length=80, blank=True)
    port = models.PositiveIntegerField(null=True, blank=True)
    protocol = models.CharField(max_length=20, blank=True)
    url = models.URLField(blank=True)
    suggested_remediation = models.TextField(blank=True)
    cve_ids = models.JSONField(default=list, blank=True)
    cwe_ids = models.JSONField(default=list, blank=True)
    references = models.JSONField(default=list, blank=True)
    raw_location = models.CharField(max_length=500, blank=True)
    first_seen_at = models.DateTimeField()
    last_seen_at = models.DateTimeField()
    first_seen_import = models.ForeignKey(
        ScanImport,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="first_seen_observations",
    )
    last_seen_import = models.ForeignKey(
        ScanImport,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="last_seen_observations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["assessment", "fingerprint"],
                name="unique_observation_fingerprint_per_assessment",
            )
        ]
        ordering = ["-last_seen_at", "title"]

    def __str__(self) -> str:
        return self.title


class ScanImportObservation(models.Model):
    class State(models.TextChoices):
        CREATED = "CREATED", "Created"
        REOBSERVED = "REOBSERVED", "Re-observed"

    scan_import = models.ForeignKey(
        ScanImport,
        on_delete=models.CASCADE,
        related_name="import_observations",
    )
    scanner_observation = models.ForeignKey(
        ScannerObservation,
        on_delete=models.CASCADE,
        related_name="import_links",
    )
    state = models.CharField(max_length=20, choices=State.choices)
    observed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["scan_import", "scanner_observation"],
                name="unique_observation_per_scan_import",
            )
        ]
        ordering = ["-observed_at"]


class FindingSource(models.Model):
    finding = models.ForeignKey(
        "findings.Finding",
        on_delete=models.CASCADE,
        related_name="sources",
    )
    scanner_observation = models.ForeignKey(
        ScannerObservation,
        on_delete=models.PROTECT,
        related_name="finding_sources",
    )
    first_seen_at = models.DateTimeField()
    last_seen_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["finding", "scanner_observation"],
                name="unique_finding_observation_source",
            )
        ]
