from django.test import TestCase, override_settings

from apps.assessments.models import Asset
from apps.common.exceptions import ImportValidationError
from apps.imports.models import ScanImport, ScannerObservation
from apps.imports.parsers.nessus import NessusXmlImporter

from .helpers import ImportTestDataMixin


@override_settings(MAX_IMPORT_FILE_SIZE_BYTES=5 * 1024 * 1024)
class NessusXmlImporterTests(ImportTestDataMixin, TestCase):
    def setUp(self):
        self.importer = NessusXmlImporter(max_size_bytes=5 * 1024 * 1024)

    def sample_content(self):
        with open("fixtures/nessus/sample.nessus", "rb") as fixture:
            return fixture.read()

    def test_valid_fixture_produces_normalised_observations(self):
        observations = self.importer.parse(self.sample_content())

        self.assertEqual(len(observations), 2)
        tls = next(item for item in observations if item.scanner_plugin_id == "42873")
        ssh = next(item for item in observations if item.scanner_plugin_id == "10287")
        self.assertEqual(tls.source_tool, "NESSUS")
        self.assertEqual(tls.title, "SSL Medium Strength Cipher Suites Supported")
        self.assertEqual(tls.raw_severity, "MEDIUM")
        self.assertEqual(tls.asset_identifier, "10.10.10.15")
        self.assertEqual(tls.hostname, "training-server.local")
        self.assertEqual(tls.port, 443)
        self.assertEqual(tls.protocol, "tcp")
        self.assertEqual(tls.raw_location, "10.10.10.15:443/tcp (https)")
        self.assertEqual(tls.cve_ids, ["CVE-2024-12345"])
        self.assertEqual(tls.cwe_ids, ["CWE-326"])
        self.assertEqual(tls.candidate_cvss_score, "5.0")
        self.assertIn("Candidate CVSS score: 5.0", tls.evidence_summary)
        self.assertEqual(ssh.cve_ids, [])
        self.assertEqual(ssh.raw_severity, "LOW")

    def test_missing_optional_fields_do_not_crash(self):
        content = b"<?xml version='1.0'?><NessusClientData_v2><Report><ReportHost name='training-server.local'><HostProperties><tag name='host-fqdn'>training-server.local</tag></HostProperties><ReportItem pluginID='999' pluginName='Minimal Plugin' severity='0' /></ReportHost></Report></NessusClientData_v2>"

        observations = self.importer.parse(content)

        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0].asset_identifier, "training-server.local")
        self.assertEqual(observations[0].raw_severity, "INFORMATIONAL")
        self.assertIsNone(observations[0].port)

    def test_invalid_inputs_fail_safely(self):
        cases = [
            (b"<NessusClientData_v2 />", "sample.xml"),
            (b"", "sample.nessus"),
            (b"<NessusClientData_v2><Report>", "sample.nessus"),
            (b"<!DOCTYPE foo><NessusClientData_v2 />", "sample.nessus"),
            (b"<!ENTITY xxe SYSTEM 'file:///etc/passwd'><NessusClientData_v2 />", "sample.nessus"),
            (b"<notnessus />", "sample.nessus"),
            (b"<NessusClientData_v2><Report /></NessusClientData_v2>", "sample.nessus"),
            (b"<NessusClientData_v2><Report><ReportHost name='x' /></Report></NessusClientData_v2>", "sample.nessus"),
        ]

        for content, filename in cases:
            with self.subTest(filename=filename, content=content[:20]):
                with self.assertRaises(ImportValidationError):
                    self.importer.validate(content, filename)

    def test_oversized_input_fails_before_parsing(self):
        importer = NessusXmlImporter(max_size_bytes=10)

        with self.assertRaises(ImportValidationError):
            importer.validate(self.sample_content(), "sample.nessus")

    def test_raw_plugin_output_and_fake_secrets_are_not_returned(self):
        observations = self.importer.parse(self.sample_content())
        combined = " ".join(
            f"{item.title} {item.description} {item.evidence_summary} {item.suggested_remediation} {item.raw_location}"
            for item in observations
        )

        self.assertNotIn("plugin_output", combined)
        self.assertNotIn("token=should-not-persist", combined)
        self.assertNotIn("password=should-not-persist", combined)
        self.assertNotIn("<p>", combined)
        self.assertIn("fictional training service", combined)

    def test_parser_does_not_persist_models(self):
        self.importer.parse(self.sample_content())

        self.assertEqual(ScanImport.objects.count(), 0)
        self.assertEqual(ScannerObservation.objects.count(), 0)
        self.assertEqual(Asset.objects.count(), 0)
