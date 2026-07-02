from django.db import IntegrityError
from django.test import TestCase, override_settings

from apps.assessments.models import Asset
from apps.common.exceptions import ImportValidationError
from apps.findings.models import Finding
from apps.imports.models import FindingSource, ScanImport, ScanImportObservation, ScannerObservation
from apps.imports.services.import_service import import_report

from .helpers import ImportTestDataMixin


@override_settings(MAX_IMPORT_FILE_SIZE_BYTES=5 * 1024 * 1024)
class ImportServiceTests(ImportTestDataMixin, TestCase):
    def setUp(self):
        self.create_import_domain()

    def import_sample(self, actor=None):
        return import_report(
            assessment=self.assessment_a,
            actor=actor or self.consultant_a,
            tool="nmap",
            filename="sample.xml",
            content=self.sample_content(),
        )

    def test_authorised_consultant_import_creates_metadata_assets_and_observations(self):
        scan_import = self.import_sample()

        self.assertEqual(scan_import.status, ScanImport.Status.COMPLETED)
        self.assertEqual(scan_import.source_filename, "sample.xml")
        self.assertEqual(len(scan_import.file_sha256), 64)
        self.assertEqual(scan_import.observations_created, 3)
        self.assertEqual(scan_import.observations_updated, 0)
        self.assertEqual(Asset.objects.filter(assessment=self.assessment_a).count(), 1)
        self.assertEqual(ScannerObservation.objects.filter(assessment=self.assessment_a).count(), 3)
        self.assertEqual(ScanImportObservation.objects.filter(scan_import=scan_import).count(), 3)
        self.assertEqual(Finding.objects.count(), 0)

    def test_reimport_deduplicates_assets_and_canonical_observations_but_preserves_history(self):
        first_import = self.import_sample()
        first_observation = ScannerObservation.objects.get(scanner_plugin_id="ssl-enum-ciphers")

        second_import = self.import_sample()
        first_observation.refresh_from_db()

        self.assertNotEqual(first_import.id, second_import.id)
        self.assertEqual(Asset.objects.filter(assessment=self.assessment_a).count(), 1)
        self.assertEqual(ScannerObservation.objects.filter(assessment=self.assessment_a).count(), 3)
        self.assertEqual(ScanImportObservation.objects.count(), 6)
        self.assertEqual(second_import.observations_created, 0)
        self.assertEqual(second_import.observations_updated, 3)
        self.assertEqual(first_observation.last_seen_import, second_import)

    def test_unassigned_consultant_manager_and_client_user_cannot_import(self):
        for actor in [self.consultant_b, self.manager_a, self.client_user_a]:
            with self.subTest(actor=actor.email):
                with self.assertRaises(ImportValidationError):
                    import_report(
                        assessment=self.assessment_a,
                        actor=actor,
                        tool="nmap",
                        filename="sample.xml",
                        content=self.sample_content(),
                    )

    def test_validation_failure_creates_no_partial_records(self):
        with self.assertRaises(ImportValidationError):
            import_report(
                assessment=self.assessment_a,
                actor=self.consultant_a,
                tool="nmap",
                filename="bad.xml",
                content=b"<nmaprun><host>",
            )

        self.assertEqual(ScanImport.objects.count(), 0)
        self.assertEqual(ScannerObservation.objects.count(), 0)

    def test_finding_source_unique_constraint_exists(self):
        scan_import = self.import_sample()
        observation = ScannerObservation.objects.first()
        finding = Finding.objects.create(
            assessment=self.assessment_a,
            affected_asset=observation.asset,
            title="Confirmed fictional issue",
            description="Confirmed during later triage.",
            cvss_score="5.0",
            business_impact="Fictional impact.",
            remediation="Fictional remediation.",
            created_by=self.consultant_a,
        )
        FindingSource.objects.create(
            finding=finding,
            scanner_observation=observation,
            first_seen_at=scan_import.created_at,
            last_seen_at=scan_import.created_at,
        )

        with self.assertRaises(IntegrityError):
            FindingSource.objects.create(
                finding=finding,
                scanner_observation=observation,
                first_seen_at=scan_import.created_at,
                last_seen_at=scan_import.created_at,
            )
