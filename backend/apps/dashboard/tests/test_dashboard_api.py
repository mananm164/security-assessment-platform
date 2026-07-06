from datetime import date, timedelta

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.findings.models import Finding
from apps.imports.models import FindingSource, ScannerObservation
from apps.imports.services.import_service import import_report

from apps.imports.tests.helpers import ImportTestDataMixin


@override_settings(MAX_IMPORT_FILE_SIZE_BYTES=5 * 1024 * 1024)
class DashboardApiTests(ImportTestDataMixin, TestCase):
    def setUp(self):
        self.api = APIClient()
        self.create_import_domain()
        self.scan_import = import_report(
            assessment=self.assessment_a,
            actor=self.consultant_a,
            tool="nmap",
            filename="sample.xml",
            content=self.sample_content(),
        )
        self.observation = ScannerObservation.objects.get(scanner_plugin_id="ssl-enum-ciphers")
        self.finding = Finding.objects.create(
            assessment=self.assessment_a,
            affected_asset=self.observation.asset,
            title="Dashboard finding",
            description="Fictional description.",
            cvss_score="9.0",
            business_impact="Fictional impact.",
            remediation="Fictional remediation.",
            remediation_owner="Web Team",
            due_date=timezone.localdate() - timedelta(days=1),
            priority_score=92,
            priority_label="URGENT",
            created_by=self.consultant_a,
        )
        FindingSource.objects.create(
            finding=self.finding,
            scanner_observation=self.observation,
            first_seen_at=self.observation.first_seen_at,
            last_seen_at=self.observation.last_seen_at,
        )

    def test_consultant_dashboard_returns_management_metrics(self):
        self.api.force_authenticate(self.consultant_a)

        response = self.api.get(reverse("dashboard-summary"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["metrics"]["open_findings"], 1)
        self.assertEqual(body["metrics"]["critical_high_findings"], 1)
        self.assertEqual(body["metrics"]["overdue_remediations"], 1)
        self.assertEqual(body["severity_distribution"][0]["severity"], "CRITICAL")
        self.assertEqual(body["source_distribution"][0]["source_tool"], "NMAP")
        self.assertEqual(len(body["recent_imports"]), 1)
        self.assertEqual(body["top_priority_findings"][0]["id"], self.finding.id)

    def test_client_dashboard_is_read_only_and_hides_raw_imports(self):
        self.api.force_authenticate(self.client_user_a)

        response = self.api.get(reverse("dashboard-summary"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["metrics"]["open_findings"], 1)
        self.assertNotIn("recent_imports", body["metrics"])
        self.assertEqual(body["recent_imports"], [])
        self.assertNotIn("recent_activity", body)

    def test_unassigned_consultant_does_not_see_other_client_metrics(self):
        self.api.force_authenticate(self.consultant_b)

        response = self.api.get(reverse("dashboard-summary"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["metrics"]["open_findings"], 0)
