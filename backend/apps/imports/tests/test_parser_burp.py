from django.test import TestCase, override_settings

from apps.assessments.models import Asset
from apps.common.exceptions import ImportValidationError
from apps.imports.models import ScanImport, ScannerObservation
from apps.imports.parsers.burp import BurpXmlImporter


@override_settings(MAX_IMPORT_FILE_SIZE_BYTES=5 * 1024 * 1024)
class BurpXmlImporterTests(TestCase):
    def setUp(self):
        self.importer = BurpXmlImporter(max_size_bytes=5 * 1024 * 1024)

    def sample_content(self):
        with open("fixtures/burp/sample-issues.xml", "rb") as fixture:
            return fixture.read()

    def test_valid_fixture_with_internal_dtd_produces_observations(self):
        observations = self.importer.parse(self.sample_content())

        self.assertEqual(len(observations), 2)
        idor = next(item for item in observations if item.scanner_plugin_id == "1049088")
        header = next(item for item in observations if item.scanner_plugin_id == "524288")
        self.assertEqual(idor.source_tool, "BURP")
        self.assertEqual(idor.title, "Insecure direct object references")
        self.assertEqual(idor.asset_identifier, "https://portal.example.test")
        self.assertEqual(idor.url, "https://portal.example.test/api/invoices/12345")
        self.assertEqual(idor.raw_location, "GET /api/invoices/12345 [invoiceId]")
        self.assertEqual(idor.raw_severity, "HIGH")
        self.assertEqual(idor.confidence, "Firm")
        self.assertEqual(header.asset_identifier, "https://portal.example.test")
        self.assertEqual(header.url, "https://portal.example.test/account/profile")
        self.assertEqual(header.raw_location, "/account/profile [X-Frame-Options]")
        self.assertEqual(header.raw_severity, "LOW")
        self.assertEqual(header.confidence, "Tentative")

    def test_invalid_inputs_fail_safely(self):
        cases = [
            (b"", "sample-issues.xml"),
            (b"<issues><issue>", "sample-issues.xml"),
            (b"<notissues />", "sample-issues.xml"),
            (b"<issues />", "sample-issues.xml"),
            (b"<!DOCTYPE issues SYSTEM 'https://evil.example/dtd'><issues><issue /></issues>", "sample-issues.xml"),
            (b"<!DOCTYPE issues PUBLIC '-//evil//DTD X//EN' 'https://evil.example/dtd'><issues><issue /></issues>", "sample-issues.xml"),
            (b"<!DOCTYPE issues [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]><issues><issue /></issues>", "sample-issues.xml"),
            (b"<!DOCTYPE issues [<!ELEMENT issues (issue*)>]><issues><issue /></issues>", "sample.txt"),
        ]

        for content, filename in cases:
            with self.subTest(filename=filename, content=content[:30]):
                with self.assertRaises(ImportValidationError):
                    self.importer.validate(content, filename)

    def test_parameter_entity_reference_fails_safely(self):
        content = b"<!DOCTYPE issues [<!ELEMENT issues (issue*)> %evil;]><issues><issue /></issues>"

        with self.assertRaises(ImportValidationError):
            self.importer.validate(content, "sample-issues.xml")

    def test_oversized_input_fails_before_parsing(self):
        importer = BurpXmlImporter(max_size_bytes=10)

        with self.assertRaises(ImportValidationError):
            importer.validate(self.sample_content(), "sample-issues.xml")

    def test_request_response_and_fake_secrets_are_not_returned(self):
        observations = self.importer.parse(self.sample_content())
        combined = " ".join(
            f"{item.title} {item.description} {item.evidence_summary} {item.suggested_remediation} {item.raw_location} {item.url}"
            for item in observations
        )

        self.assertNotIn("Authorization", combined)
        self.assertNotIn("Cookie", combined)
        self.assertNotIn("should-not-persist", combined)
        self.assertNotIn("password=", combined)
        self.assertNotIn("fictional response body", combined)
        self.assertNotIn("<p>", combined)
        self.assertIn("fictional portal", combined)

    def test_parser_does_not_persist_models(self):
        self.importer.parse(self.sample_content())

        self.assertEqual(ScanImport.objects.count(), 0)
        self.assertEqual(ScannerObservation.objects.count(), 0)
        self.assertEqual(Asset.objects.count(), 0)
