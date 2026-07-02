from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from apps.imports.models import ScanImport, ScannerObservation

from .helpers import FIXTURE_PATH, ImportTestDataMixin


@override_settings(MAX_IMPORT_FILE_SIZE_BYTES=5 * 1024 * 1024)
class ImportScanCommandTests(ImportTestDataMixin, TestCase):
    def setUp(self):
        self.create_import_domain()

    def test_valid_command_imports_fixture_safely(self):
        stdout = StringIO()

        call_command(
            "import_scan",
            assessment_id=self.assessment_a.id,
            tool="nmap",
            file=str(FIXTURE_PATH),
            actor_email=self.consultant_a.email,
            stdout=stdout,
        )

        output = stdout.getvalue()
        self.assertIn("Imported Nmap report", output)
        self.assertIn("Observations created: 3", output)
        self.assertNotIn("<nmaprun", output)
        self.assertEqual(ScanImport.objects.count(), 1)
        self.assertEqual(ScannerObservation.objects.count(), 3)

    def test_valid_zap_command_imports_fixture_safely(self):
        stdout = StringIO()

        call_command(
            "import_scan",
            assessment_id=self.assessment_a.id,
            tool="zap",
            file="fixtures/zap/traditional-report.json",
            actor_email=self.consultant_a.email,
            stdout=stdout,
        )

        output = stdout.getvalue()
        self.assertIn("Imported Zap report", output)
        self.assertIn("Observations created: 3", output)
        self.assertNotIn("attack", output)
        self.assertEqual(ScanImport.objects.count(), 1)
        self.assertEqual(ScannerObservation.objects.count(), 3)



    def test_valid_nessus_command_imports_fixture_safely(self):
        stdout = StringIO()

        call_command(
            "import_scan",
            assessment_id=self.assessment_a.id,
            tool="nessus",
            file="fixtures/nessus/sample.nessus",
            actor_email=self.consultant_a.email,
            stdout=stdout,
        )

        output = stdout.getvalue()
        self.assertIn("Imported Nessus report", output)
        self.assertIn("Observations created: 2", output)
        self.assertNotIn("token=should-not-persist", output)
        self.assertEqual(ScanImport.objects.count(), 1)
        self.assertEqual(ScannerObservation.objects.count(), 2)


    def test_valid_burp_command_imports_fixture_safely(self):
        stdout = StringIO()

        call_command(
            "import_scan",
            assessment_id=self.assessment_a.id,
            tool="burp",
            file="fixtures/burp/sample-issues.xml",
            actor_email=self.consultant_a.email,
            stdout=stdout,
        )

        output = stdout.getvalue()
        self.assertIn("Imported Burp report", output)
        self.assertIn("Observations created: 2", output)
        self.assertNotIn("should-not-persist", output)
        self.assertEqual(ScanImport.objects.count(), 1)
        self.assertEqual(ScannerObservation.objects.count(), 2)

    def test_unknown_actor_email_fails_safely(self):
        with self.assertRaisesMessage(CommandError, "actor email was not found"):
            call_command(
                "import_scan",
                assessment_id=self.assessment_a.id,
                tool="nmap",
                file=str(FIXTURE_PATH),
                actor_email="missing@example.test",
            )

    def test_unknown_assessment_id_fails_safely(self):
        with self.assertRaisesMessage(CommandError, "assessment was not found"):
            call_command(
                "import_scan",
                assessment_id=999999,
                tool="nmap",
                file=str(FIXTURE_PATH),
                actor_email=self.consultant_a.email,
            )

    def test_unsupported_tool_fails_safely(self):
        with self.assertRaisesMessage(CommandError, "Unsupported scanner import tool"):
            call_command(
                "import_scan",
                assessment_id=self.assessment_a.id,
                tool="arachni",
                file=str(FIXTURE_PATH),
                actor_email=self.consultant_a.email,
            )
