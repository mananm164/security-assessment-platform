import json

from django.test import TestCase, override_settings

from apps.common.exceptions import ImportValidationError
from apps.imports.models import ScanImport, ScannerObservation
from apps.imports.parsers.zap import ZapJsonImporter, canonical_url, strip_html


@override_settings(MAX_IMPORT_FILE_SIZE_BYTES=5 * 1024 * 1024)
class ZapParserTests(TestCase):
    def setUp(self):
        self.importer = ZapJsonImporter(max_size_bytes=5 * 1024 * 1024)

    def sample_content(self):
        with open("fixtures/zap/traditional-report.json", "rb") as fixture:
            return fixture.read()

    def test_valid_traditional_report_parses_alert_instances(self):
        observations = self.importer.parse(self.sample_content())

        self.assertEqual(len(observations), 3)
        xss = [item for item in observations if item.scanner_plugin_id == "40012"]
        self.assertEqual(len(xss), 2)
        self.assertEqual(xss[0].source_tool, "ZAP")
        self.assertEqual(xss[0].raw_severity, "HIGH")
        self.assertEqual(xss[0].confidence, "Medium")
        self.assertEqual(xss[0].cwe_ids, ["79"])
        self.assertEqual(xss[0].asset_identifier, "https://training-web.local:8443")

    def test_invalid_json_wrong_extension_blank_and_bad_site_fail_safely(self):
        cases = [
            (b"", "zap.json"),
            (self.sample_content(), "zap.txt"),
            (b"not-json", "zap.json"),
            (json.dumps({"site": {}}).encode(), "zap.json"),
        ]

        for content, filename in cases:
            with self.subTest(filename=filename):
                with self.assertRaises(ImportValidationError) as raised:
                    self.importer.validate(content, filename)
                self.assertNotIn("Traceback", str(raised.exception))
                self.assertNotIn("not-json", str(raised.exception))

    def test_oversized_input_is_rejected(self):
        importer = ZapJsonImporter(max_size_bytes=10)

        with self.assertRaises(ImportValidationError):
            importer.validate(self.sample_content(), "zap.json")

    def test_raw_http_message_format_is_rejected(self):
        payload = {"site": [{"alerts": [{"instances": [{"requestHeader": "GET / HTTP/1.1"}]}]}]}

        with self.assertRaisesMessage(ImportValidationError, "raw HTTP messages"):
            self.importer.validate(json.dumps(payload).encode(), "zap.json")

    def test_html_is_stripped_and_urls_are_canonicalised(self):
        self.assertEqual(strip_html("<p>Hello <strong>world</strong></p>"), "Hello world")
        self.assertEqual(
            canonical_url("https://training-web.local:8443/search?q=payload#frag"),
            "https://training-web.local:8443/search",
        )

    def test_payload_fields_and_query_values_are_not_in_observations(self):
        observations = self.importer.parse(self.sample_content())
        serialised = "\n".join(
            [
                item.external_id
                + item.description
                + item.evidence_summary
                + item.raw_location
                + item.url
                for item in observations
            ]
        )

        self.assertNotIn("alert(1)", serialised)
        self.assertNotIn("secret-token", serialised)
        self.assertNotIn("payload", serialised)
        self.assertNotIn("<p>", serialised)
        self.assertIn("param:q", serialised)

    def test_parser_does_not_persist_database_records(self):
        self.importer.validate(self.sample_content(), "zap.json")
        self.importer.parse(self.sample_content())

        self.assertEqual(ScanImport.objects.count(), 0)
        self.assertEqual(ScannerObservation.objects.count(), 0)
