from django.db import models


class VulnerabilityIntel(models.Model):
    class RefreshStatus(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        PARTIAL = "PARTIAL", "Partial"
        FAILED = "FAILED", "Failed"

    cve_id = models.CharField(max_length=40, unique=True)
    nvd_description = models.TextField(null=True, blank=True)
    nvd_cvss_score = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    nvd_cvss_vector = models.CharField(max_length=255, null=True, blank=True)
    cwe_ids = models.JSONField(default=list, blank=True)
    references = models.JSONField(default=list, blank=True)
    kev_listed = models.BooleanField(default=False)
    kev_date_added = models.DateField(null=True, blank=True)
    epss_score = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    epss_percentile = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    source_retrieved_at = models.DateTimeField(null=True, blank=True)
    last_refresh_attempt_at = models.DateTimeField(null=True, blank=True)
    last_refresh_status = models.CharField(max_length=20, choices=RefreshStatus.choices, default=RefreshStatus.FAILED)
    last_safe_error = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["cve_id"]
        indexes = [models.Index(fields=["cve_id"])]

    def save(self, *args, **kwargs):
        self.cve_id = self.cve_id.upper().strip()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.cve_id
