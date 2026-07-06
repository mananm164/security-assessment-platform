from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.findings.models import Finding
from apps.imports.models import ScanImport, ScannerObservation
from apps.imports.services.import_service import import_report

from apps.imports.tests.helpers import ImportTestDataMixin


@override_settings(MAX_IMPORT_FILE_SIZE_BYTES=5 * 1024 * 1024)
class AuditWorkflowTests(ImportTestDataMixin, TestCase):
    def setUp(self):
        self.api = APIClient()
        self.create_import_domain()

    def import_sample(self):
        return import_report(
            assessment=self.assessment_a,
            actor=self.consultant_a,
            tool="nmap",
            filename="sample.xml",
            content=self.sample_content(),
        )

    def test_import_triage_promotion_and_finding_update_create_audit_events(self):
        scan_import = self.import_sample()
        observation = ScannerObservation.objects.get(scanner_plugin_id="ssl-enum-ciphers")
        self.api.force_authenticate(self.consultant_a)

        triage_response = self.api.post(
            reverse("scannerobservation-triage", args=[observation.id]),
            {"triage_status": "CONFIRMED", "triage_note": "Validated during review."},
            format="json",
        )
        promote_response = self.api.post(
            reverse("scannerobservation-promote", args=[observation.id]),
            {
                "cvss_score": "7.5",
                "business_impact": "Fictional impact.",
                "remediation_owner": "Web Team",
                "due_date": "2026-07-24",
            },
            format="json",
        )
        finding_id = promote_response.json()["id"]
        update_response = self.api.patch(
            reverse("finding-detail", args=[finding_id]),
            {
                "status": Finding.Status.IN_PROGRESS,
                "remediation_owner": "Platform Team",
                "due_date": "2026-07-25",
                "business_impact": "Updated fictional impact.",
                "remediation": "Updated fictional remediation notes.",
            },
            format="json",
        )

        self.assertEqual(triage_response.status_code, status.HTTP_200_OK)
        self.assertEqual(promote_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.SCAN_IMPORT_CREATED, entity_id=scan_import.id).exists())
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.OBSERVATION_TRIAGED, entity_id=observation.id).exists())
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.OBSERVATION_PROMOTED, entity_id=finding_id).exists())
        update_log = AuditLog.objects.get(action=AuditLog.Action.FINDING_UPDATED, entity_id=finding_id)
        self.assertIn("status", update_log.safe_metadata["changed_fields"])
        self.assertNotIn("Updated fictional impact", str(update_log.safe_metadata))

    def test_audit_log_api_is_tenant_scoped(self):
        self.import_sample()
        log = AuditLog.objects.get(action=AuditLog.Action.SCAN_IMPORT_CREATED)

        self.api.force_authenticate(self.consultant_a)
        allowed = self.api.get(reverse("auditlog-list"), {"assessment": self.assessment_a.id})
        self.api.force_authenticate(self.consultant_b)
        denied = self.api.get(reverse("auditlog-detail", args=[log.id]))

        self.assertEqual(allowed.status_code, status.HTTP_200_OK)
        self.assertEqual(len(allowed.json()["results"]), 1)
        self.assertEqual(denied.status_code, status.HTTP_404_NOT_FOUND)

    def test_manager_reads_audit_but_cannot_update_finding(self):
        scan_import = self.import_sample()
        observation = scan_import.import_observations.first().scanner_observation
        finding = Finding.objects.create(
            assessment=self.assessment_a,
            affected_asset=observation.asset,
            title="Manager visible finding",
            description="Fictional description.",
            cvss_score="5.0",
            business_impact="Fictional impact.",
            remediation="Fictional remediation.",
            created_by=self.consultant_a,
        )
        self.api.force_authenticate(self.manager_a)

        audit_response = self.api.get(reverse("auditlog-list"), {"entity_type": "SCAN_IMPORT", "entity_id": scan_import.id})
        patch_response = self.api.patch(reverse("finding-detail", args=[finding.id]), {"status": "IN_PROGRESS"}, format="json")

        self.assertEqual(audit_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.status_code, status.HTTP_403_FORBIDDEN)
