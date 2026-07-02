from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.assessments.models import Asset
from apps.common.exceptions import ImportValidationError
from apps.findings.models import Finding
from apps.imports.models import FindingSource, ScanImport, ScanImportObservation, ScannerObservation
from apps.imports.services.import_service import import_report

from .helpers import ImportTestDataMixin


@override_settings(MAX_IMPORT_FILE_SIZE_BYTES=5 * 1024 * 1024)
class BurpImportWorkflowTests(ImportTestDataMixin, TestCase):
    def setUp(self):
        self.api = APIClient()
        self.create_import_domain()

    def burp_content(self):
        with open("fixtures/burp/sample-issues.xml", "rb") as fixture:
            return fixture.read()

    def import_burp(self, actor=None, assessment=None):
        return import_report(
            assessment=assessment or self.assessment_a,
            actor=actor or self.consultant_a,
            tool="burp",
            filename="sample-issues.xml",
            content=self.burp_content(),
        )

    def test_assigned_consultant_imports_burp_and_reimport_deduplicates(self):
        first_import = self.import_burp()
        second_import = self.import_burp()

        self.assertEqual(first_import.source_tool, ScanImport.SourceTool.BURP)
        self.assertEqual(len(first_import.file_sha256), 64)
        self.assertEqual(first_import.observations_created, 2)
        self.assertEqual(first_import.observations_updated, 0)
        self.assertEqual(second_import.observations_created, 0)
        self.assertEqual(second_import.observations_updated, 2)
        self.assertEqual(Asset.objects.filter(assessment=self.assessment_a, asset_type=Asset.AssetType.APPLICATION).count(), 1)
        self.assertEqual(ScannerObservation.objects.filter(assessment=self.assessment_a, source_tool=ScanImport.SourceTool.BURP).count(), 2)
        self.assertEqual(ScanImportObservation.objects.count(), 4)
        self.assertEqual(Finding.objects.count(), 0)

    def test_burp_persistence_and_api_keep_safe_fields_only(self):
        self.import_burp()
        observation = ScannerObservation.objects.get(scanner_plugin_id="1049088")
        asset = observation.asset

        self.assertEqual(asset.base_url, "https://portal.example.test")
        self.assertEqual(asset.asset_type, Asset.AssetType.APPLICATION)
        self.assertEqual(observation.raw_severity, "HIGH")
        self.assertEqual(observation.confidence, "Firm")
        self.assertEqual(observation.url, "https://portal.example.test/api/invoices/12345")
        self.assertEqual(observation.raw_location, "GET /api/invoices/12345 [invoiceId]")
        stored_text = f"{observation.description} {observation.evidence_summary} {observation.suggested_remediation} {observation.raw_location} {observation.url}"
        self.assertNotIn("Authorization", stored_text)
        self.assertNotIn("Cookie", stored_text)
        self.assertNotIn("should-not-persist", stored_text)
        self.assertNotIn("password=", stored_text)

        self.api.force_authenticate(self.consultant_a)
        response = self.api.get(reverse("scannerobservation-list"), {"source_tool": "BURP"})
        response_text = str(response.json())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("Authorization", response_text)
        self.assertNotIn("Cookie", response_text)
        self.assertNotIn("should-not-persist", response_text)

    def test_admin_can_import_and_unassigned_roles_cannot_import_burp(self):
        admin_import = self.import_burp(actor=self.admin, assessment=self.assessment_b)
        self.assertEqual(admin_import.source_tool, ScanImport.SourceTool.BURP)

        for actor in [self.consultant_b, self.manager_a, self.client_user_a]:
            with self.subTest(actor=actor.email):
                with self.assertRaises(ImportValidationError):
                    self.import_burp(actor=actor)

    def test_reimport_preserves_existing_triage_status(self):
        self.import_burp()
        observation = ScannerObservation.objects.get(scanner_plugin_id="1049088")
        self.api.force_authenticate(self.consultant_a)
        response = self.api.post(
            reverse("scannerobservation-triage", args=[observation.id]),
            {"triage_status": "FALSE_POSITIVE", "triage_note": "Compensating control confirmed."},
            format="json",
        )

        second_import = self.import_burp()
        observation.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(observation.triage_status, ScannerObservation.TriageStatus.FALSE_POSITIVE)
        self.assertEqual(observation.triage_note, "Compensating control confirmed.")
        self.assertEqual(observation.last_seen_import, second_import)

    def test_api_filtering_triage_and_promotion_work_for_burp(self):
        self.import_burp()
        observation = ScannerObservation.objects.get(scanner_plugin_id="1049088")

        self.api.force_authenticate(self.consultant_a)
        imports_response = self.api.get(reverse("scanimport-list"), {"source_tool": "BURP"})
        observations_response = self.api.get(reverse("scannerobservation-list"), {"source_tool": "BURP"})
        triage_response = self.api.post(
            reverse("scannerobservation-triage", args=[observation.id]),
            {"triage_status": "CONFIRMED", "triage_note": "Validated during authorised Burp review."},
            format="json",
        )
        promote_response = self.api.post(
            reverse("scannerobservation-promote", args=[observation.id]),
            {
                "cvss_score": "8.1",
                "business_impact": "A fictional user could access another user's invoice.",
                "remediation_owner": "Web Platform Team",
                "due_date": "2026-07-24",
            },
            format="json",
        )
        second_import = self.import_burp()

        self.assertEqual(imports_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(imports_response.json()["results"]), 1)
        self.assertEqual(observations_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(observations_response.json()["results"]), 2)
        self.assertEqual(triage_response.status_code, status.HTTP_200_OK)
        self.assertEqual(promote_response.status_code, status.HTTP_201_CREATED)
        finding = Finding.objects.get(id=promote_response.json()["id"])
        self.assertEqual(finding.severity, Finding.Severity.HIGH)
        self.assertEqual(FindingSource.objects.filter(finding=finding, scanner_observation=observation).count(), 1)
        observation.refresh_from_db()
        self.assertEqual(observation.triage_status, ScannerObservation.TriageStatus.PROMOTED)
        self.assertEqual(second_import.observations_created, 0)
        self.assertEqual(second_import.observations_updated, 2)
        self.assertEqual(Asset.objects.filter(assessment=self.assessment_a).count(), 1)
        self.assertEqual(ScannerObservation.objects.filter(assessment=self.assessment_a, source_tool=ScanImport.SourceTool.BURP).count(), 2)
        self.assertEqual(Finding.objects.count(), 1)

    def test_manager_and_client_user_cannot_modify_burp_observations(self):
        self.import_burp()
        observation = ScannerObservation.objects.get(scanner_plugin_id="1049088")

        for actor in [self.manager_a, self.client_user_a]:
            with self.subTest(actor=actor.email):
                self.api.force_authenticate(actor)
                triage_response = self.api.post(
                    reverse("scannerobservation-triage", args=[observation.id]),
                    {"triage_status": "CONFIRMED", "triage_note": "reviewed"},
                    format="json",
                )
                promote_response = self.api.post(
                    reverse("scannerobservation-promote", args=[observation.id]),
                    {
                        "cvss_score": "8.1",
                        "business_impact": "Impact.",
                        "remediation_owner": "Team",
                        "due_date": "2026-07-24",
                    },
                    format="json",
                )
                expected = status.HTTP_404_NOT_FOUND if actor == self.client_user_a else status.HTTP_403_FORBIDDEN
                self.assertEqual(triage_response.status_code, expected)
                self.assertEqual(promote_response.status_code, expected)
