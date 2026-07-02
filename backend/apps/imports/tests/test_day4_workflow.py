from datetime import date

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.assessments.models import Asset, Assessment
from apps.findings.models import Finding
from apps.imports.models import FindingSource, ScanImport, ScanImportObservation, ScannerObservation
from apps.imports.services.import_service import import_report

from .helpers import ImportTestDataMixin


@override_settings(MAX_IMPORT_FILE_SIZE_BYTES=5 * 1024 * 1024)
class ZapImportTriagePromotionTests(ImportTestDataMixin, TestCase):
    def setUp(self):
        self.api = APIClient()
        self.create_import_domain()

    def zap_content(self):
        with open("fixtures/zap/traditional-report.json", "rb") as fixture:
            return fixture.read()

    def import_zap(self, actor=None):
        return import_report(
            assessment=self.assessment_a,
            actor=actor or self.consultant_a,
            tool="zap",
            filename="traditional-report.json",
            content=self.zap_content(),
        )

    def test_assigned_consultant_imports_zap_and_reimport_deduplicates(self):
        first_import = self.import_zap()
        second_import = self.import_zap()

        self.assertEqual(first_import.source_tool, ScanImport.SourceTool.ZAP)
        self.assertEqual(first_import.observations_created, 3)
        self.assertEqual(second_import.observations_created, 0)
        self.assertEqual(second_import.observations_updated, 3)
        self.assertEqual(Asset.objects.filter(assessment=self.assessment_a, asset_type=Asset.AssetType.APPLICATION).count(), 1)
        self.assertEqual(ScannerObservation.objects.filter(assessment=self.assessment_a, source_tool=ScanImport.SourceTool.ZAP).count(), 3)
        self.assertEqual(ScanImportObservation.objects.count(), 6)
        self.assertEqual(Finding.objects.count(), 0)

    def test_zap_persistence_keeps_safe_fields_only(self):
        self.import_zap()
        observation = ScannerObservation.objects.get(scanner_plugin_id="40012", raw_location__contains="param:q")

        self.assertEqual(observation.raw_severity, "HIGH")
        self.assertEqual(observation.confidence, "Medium")
        self.assertEqual(observation.url, "https://training-web.local:8443/search")
        self.assertEqual(observation.cwe_ids, ["79"])
        self.assertIn("Encode output", observation.suggested_remediation)
        stored_text = f"{observation.description} {observation.evidence_summary} {observation.raw_location} {observation.url}"
        self.assertNotIn("alert(1)", stored_text)
        self.assertNotIn("<p>", stored_text)

    def test_unassigned_consultant_manager_and_client_user_cannot_import_zap(self):
        for actor in [self.consultant_b, self.manager_a, self.client_user_a]:
            with self.subTest(actor=actor.email):
                with self.assertRaises(Exception):
                    import_report(
                        assessment=self.assessment_a,
                        actor=actor,
                        tool="zap",
                        filename="traditional-report.json",
                        content=self.zap_content(),
                    )

    def test_consultant_can_confirm_false_positive_and_duplicate_with_rules(self):
        self.import_zap()
        observations = list(ScannerObservation.objects.filter(source_tool=ScanImport.SourceTool.ZAP).order_by("id"))
        self.api.force_authenticate(self.consultant_a)

        confirm_response = self.api.post(
            reverse("scannerobservation-triage", args=[observations[0].id]),
            {"triage_status": ScannerObservation.TriageStatus.CONFIRMED, "triage_note": "Reproduced safely."},
            format="json",
        )
        false_without_note = self.api.post(
            reverse("scannerobservation-triage", args=[observations[1].id]),
            {"triage_status": ScannerObservation.TriageStatus.FALSE_POSITIVE, "triage_note": ""},
            format="json",
        )
        false_response = self.api.post(
            reverse("scannerobservation-triage", args=[observations[1].id]),
            {"triage_status": ScannerObservation.TriageStatus.FALSE_POSITIVE, "triage_note": "Reverse proxy mitigates it."},
            format="json",
        )
        duplicate_response = self.api.post(
            reverse("scannerobservation-triage", args=[observations[2].id]),
            {
                "triage_status": ScannerObservation.TriageStatus.DUPLICATE,
                "duplicate_of_id": observations[0].id,
                "triage_note": "Same affected application pattern.",
            },
            format="json",
        )

        self.assertEqual(confirm_response.status_code, status.HTTP_200_OK)
        self.assertEqual(false_without_note.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(false_response.status_code, status.HTTP_200_OK)
        self.assertEqual(duplicate_response.status_code, status.HTTP_200_OK)

    def test_duplicate_requires_same_assessment_and_not_self(self):
        self.import_zap()
        other_assessment = Assessment.objects.create(
            client=self.client_a,
            name="Second Northwind Assessment",
            framework=Assessment.Framework.OWASP,
            status=Assessment.Status.ACTIVE,
            start_date=date(2026, 7, 3),
            scope_summary="Fictional second assessment.",
            created_by=self.consultant_a,
        )
        other_import = import_report(
            assessment=other_assessment,
            actor=self.consultant_a,
            tool="zap",
            filename="traditional-report.json",
            content=self.zap_content(),
        )
        observation = ScannerObservation.objects.filter(assessment=self.assessment_a).first()
        other_observation = other_import.import_observations.first().scanner_observation
        self.api.force_authenticate(self.consultant_a)

        self_response = self.api.post(
            reverse("scannerobservation-triage", args=[observation.id]),
            {"triage_status": "DUPLICATE", "duplicate_of_id": observation.id, "triage_note": "self"},
            format="json",
        )
        cross_response = self.api.post(
            reverse("scannerobservation-triage", args=[observation.id]),
            {"triage_status": "DUPLICATE", "duplicate_of_id": other_observation.id, "triage_note": "cross"},
            format="json",
        )

        self.assertEqual(self_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(cross_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_manager_and_client_user_cannot_triage_or_promote(self):
        self.import_zap()
        observation = ScannerObservation.objects.first()

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
                        "cvss_score": "7.5",
                        "business_impact": "Impact.",
                        "remediation_owner": "Team",
                        "due_date": "2026-07-20",
                    },
                    format="json",
                )
                expected = status.HTTP_404_NOT_FOUND if actor == self.client_user_a else status.HTTP_403_FORBIDDEN
                self.assertEqual(triage_response.status_code, expected)
                self.assertEqual(promote_response.status_code, expected)

    def test_confirmed_observation_promotes_to_one_finding_with_source(self):
        self.import_zap()
        observation = ScannerObservation.objects.get(scanner_plugin_id="40012", raw_location__contains="param:q")
        self.api.force_authenticate(self.consultant_a)
        self.api.post(
            reverse("scannerobservation-triage", args=[observation.id]),
            {"triage_status": "CONFIRMED", "triage_note": "Reproduced safely."},
            format="json",
        )

        response = self.api.post(
            reverse("scannerobservation-promote", args=[observation.id]),
            {
                "cvss_score": "7.5",
                "business_impact": "An attacker could execute script in a user session.",
                "remediation_owner": "Web Platform Team",
                "due_date": "2026-07-20",
            },
            format="json",
        )
        second_response = self.api.post(
            reverse("scannerobservation-promote", args=[observation.id]),
            {
                "cvss_score": "7.5",
                "business_impact": "Duplicate attempt.",
                "remediation_owner": "Web Platform Team",
                "due_date": "2026-07-20",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        finding = Finding.objects.get(id=response.json()["id"])
        self.assertEqual(finding.severity, Finding.Severity.HIGH)
        self.assertEqual(finding.affected_asset, observation.asset)
        self.assertEqual(FindingSource.objects.filter(finding=finding, scanner_observation=observation).count(), 1)
        observation.refresh_from_db()
        self.assertEqual(observation.triage_status, ScannerObservation.TriageStatus.PROMOTED)
        self.assertEqual(second_response.status_code, status.HTTP_400_BAD_REQUEST)
