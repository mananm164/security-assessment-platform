from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.imports.models import ImportPreview, ScanImport, ScanImportObservation, ScannerObservation
from apps.tenancy.models import ClientMembership

from .helpers import ImportTestDataMixin


FIXTURES = {
    "nmap": ("sample.xml", Path("fixtures/nmap/sample.xml")),
    "zap": ("traditional-report.json", Path("fixtures/zap/traditional-report.json")),
    "nessus": ("sample.nessus", Path("fixtures/nessus/sample.nessus")),
    "burp": ("sample-issues.xml", Path("fixtures/burp/sample-issues.xml")),
}
UNSAFE_MARKERS = [
    "<xml",
    "requestresponse",
    "cookie",
    "authorization",
    "password",
    "token",
    "payload",
    "raw plugin output",
    "?session",
    "#fragment",
]


@override_settings(MAX_IMPORT_FILE_SIZE_BYTES=5 * 1024 * 1024)
class ImportPreviewApiTests(ImportTestDataMixin, TestCase):
    def setUp(self):
        self.api = APIClient()
        self.create_import_domain()

    def upload(self, tool="nmap", filename=None, content=None, actor=None, assessment=None):
        fixture_filename, fixture_path = FIXTURES[tool]
        upload = SimpleUploadedFile(
            filename or fixture_filename,
            content if content is not None else fixture_path.read_bytes(),
            content_type="application/octet-stream",
        )
        self.api.force_authenticate(actor or self.consultant_a)
        return self.api.post(
            reverse("assessment-import-preview-list", kwargs={"assessment_id": (assessment or self.assessment_a).id}),
            {"source_tool": tool, "report_file": upload},
            format="multipart",
        )

    def test_assigned_consultant_can_create_preview_for_each_supported_fixture(self):
        for tool in FIXTURES:
            with self.subTest(tool=tool):
                response = self.upload(tool=tool)

                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                data = response.json()
                self.assertEqual(data["assessment"], self.assessment_a.id)
                self.assertEqual(data["source_tool"], tool.upper())
                self.assertGreater(data["summary"]["total_observations"], 0)
                self.assertGreater(len(data["observations"]), 0)

    def test_admin_can_create_preview_for_any_assessment(self):
        response = self.upload(tool="nmap", actor=self.admin, assessment=self.assessment_b)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["assessment"], self.assessment_b.id)

    def test_manager_client_and_unassigned_consultant_cannot_create_preview(self):
        for actor, expected in [
            (self.manager_a, status.HTTP_403_FORBIDDEN),
            (self.client_user_a, status.HTTP_403_FORBIDDEN),
            (self.consultant_b, status.HTTP_404_NOT_FOUND),
        ]:
            with self.subTest(actor=actor.email):
                response = self.upload(actor=actor)
                self.assertEqual(response.status_code, expected)

    def test_preview_read_is_limited_to_creator_or_admin(self):
        preview_id = self.upload().json()["id"]
        ClientMembership.objects.create(
            user=self.consultant_b,
            client=self.client_a,
            relationship_role=ClientMembership.RelationshipRole.CONSULTANT,
        )

        self.api.force_authenticate(self.consultant_a)
        owner_response = self.api.get(reverse("importpreview-detail", args=[preview_id]))
        self.api.force_authenticate(self.admin)
        admin_response = self.api.get(reverse("importpreview-detail", args=[preview_id]))
        self.api.force_authenticate(self.consultant_b)
        other_consultant_response = self.api.get(reverse("importpreview-detail", args=[preview_id]))
        self.api.force_authenticate(self.manager_a)
        manager_response = self.api.get(reverse("importpreview-detail", args=[preview_id]))

        self.assertEqual(owner_response.status_code, status.HTTP_200_OK)
        self.assertEqual(admin_response.status_code, status.HTTP_200_OK)
        self.assertEqual(other_consultant_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(manager_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_validation_failures_are_safe_and_create_no_preview(self):
        cases = [
            ({"source_tool": "", "report_file": SimpleUploadedFile("sample.xml", b"x")}),
            ({"source_tool": "nmap"}),
            ({"source_tool": "nmap", "report_file": SimpleUploadedFile("sample.xml", b"")}),
            ({"source_tool": "nmap", "report_file": SimpleUploadedFile("sample.json", b"{}")}),
            ({"source_tool": "arachni", "report_file": SimpleUploadedFile("sample.xml", b"x")}),
            ({"source_tool": "nmap", "report_file": SimpleUploadedFile("sample.xml", b"<nmaprun><host>")}),
        ]
        self.api.force_authenticate(self.consultant_a)

        for payload in cases:
            with self.subTest(payload=payload.keys()):
                response = self.api.post(
                    reverse("assessment-import-preview-list", kwargs={"assessment_id": self.assessment_a.id}),
                    payload,
                    format="multipart",
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(ImportPreview.objects.count(), 0)
        self.assertEqual(ScanImport.objects.count(), 0)
        self.assertEqual(ScannerObservation.objects.count(), 0)

    @override_settings(MAX_IMPORT_FILE_SIZE_BYTES=8)
    def test_oversized_file_is_rejected_before_persistence(self):
        response = self.upload(content=b"123456789", filename="sample.xml")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ImportPreview.objects.count(), 0)

    def test_preview_response_and_storage_exclude_raw_or_unsafe_markers(self):
        response = self.upload(tool="burp")
        preview = ImportPreview.objects.get(id=response.json()["id"])

        combined = (str(response.json()) + str(preview.safe_observations)).lower()
        for marker in UNSAFE_MARKERS:
            self.assertNotIn(marker, combined)

    def test_expired_preview_returns_410_and_cannot_confirm(self):
        preview_id = self.upload().json()["id"]
        ImportPreview.objects.filter(id=preview_id).update(expires_at=timezone.now() - timezone.timedelta(minutes=1))
        self.api.force_authenticate(self.consultant_a)

        read_response = self.api.get(reverse("importpreview-detail", args=[preview_id]))
        confirm_response = self.api.post(reverse("importpreview-confirm", args=[preview_id]))

        self.assertEqual(read_response.status_code, status.HTTP_410_GONE)
        self.assertEqual(confirm_response.status_code, status.HTTP_410_GONE)
        self.assertEqual(ScanImport.objects.count(), 0)

    def test_confirmation_creates_scan_import_links_audits_and_is_idempotent(self):
        preview_id = self.upload(tool="nmap").json()["id"]
        self.api.force_authenticate(self.consultant_a)

        first_response = self.api.post(reverse("importpreview-confirm", args=[preview_id]))
        second_response = self.api.post(reverse("importpreview-confirm", args=[preview_id]))
        preview = ImportPreview.objects.get(id=preview_id)

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertEqual(ScanImport.objects.count(), 1)
        self.assertEqual(ScannerObservation.objects.count(), 3)
        self.assertEqual(ScanImportObservation.objects.count(), 3)
        self.assertEqual(preview.scan_import_id, first_response.json()["scan_import_id"])
        self.assertIsNotNone(preview.confirmed_at)
        self.assertEqual(first_response.json()["observations_created"], 3)
        self.assertEqual(second_response.json()["scan_import_id"], first_response.json()["scan_import_id"])
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.IMPORT_PREVIEW_CREATED).exists())
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.IMPORT_CONFIRMED).exists())

    def test_confirming_second_preview_reobserves_existing_observations(self):
        first_preview = self.upload(tool="nmap").json()["id"]
        self.api.force_authenticate(self.consultant_a)
        self.api.post(reverse("importpreview-confirm", args=[first_preview]))

        second_preview = self.upload(tool="nmap").json()["id"]
        second_response = self.api.post(reverse("importpreview-confirm", args=[second_preview]))

        self.assertEqual(second_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.json()["observations_created"], 0)
        self.assertEqual(second_response.json()["observations_reobserved"], 3)
        self.assertEqual(ScanImport.objects.count(), 2)
        self.assertEqual(ScannerObservation.objects.count(), 3)
        self.assertEqual(ScanImportObservation.objects.count(), 6)

    def test_purge_expired_import_previews_deletes_only_unconfirmed_expired_rows(self):
        expired = ImportPreview.objects.create(
            assessment=self.assessment_a,
            source_tool=ScanImport.SourceTool.NMAP,
            source_filename="expired.xml",
            file_sha256="a" * 64,
            file_size_bytes=10,
            safe_observations=[],
            observation_count=0,
            created_by=self.consultant_a,
            expires_at=timezone.now() - timezone.timedelta(minutes=1),
        )
        active = ImportPreview.objects.create(
            assessment=self.assessment_a,
            source_tool=ScanImport.SourceTool.NMAP,
            source_filename="active.xml",
            file_sha256="b" * 64,
            file_size_bytes=10,
            safe_observations=[],
            observation_count=0,
            created_by=self.consultant_a,
            expires_at=timezone.now() + timezone.timedelta(minutes=15),
        )
        confirmed = ImportPreview.objects.create(
            assessment=self.assessment_a,
            source_tool=ScanImport.SourceTool.NMAP,
            source_filename="confirmed.xml",
            file_sha256="c" * 64,
            file_size_bytes=10,
            safe_observations=[],
            observation_count=0,
            created_by=self.consultant_a,
            confirmed_at=timezone.now(),
            confirmed_by=self.consultant_a,
            expires_at=timezone.now() - timezone.timedelta(minutes=1),
        )

        call_command("purge_expired_import_previews", verbosity=0)

        self.assertFalse(ImportPreview.objects.filter(id=expired.id).exists())
        self.assertTrue(ImportPreview.objects.filter(id=active.id).exists())
        self.assertTrue(ImportPreview.objects.filter(id=confirmed.id).exists())
