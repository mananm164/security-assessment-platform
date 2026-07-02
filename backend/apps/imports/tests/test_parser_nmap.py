from django.test import TestCase, override_settings

from apps.common.exceptions import ImportValidationError
from apps.imports.models import ScanImport, ScannerObservation
from apps.imports.parsers.nmap import NmapXmlImporter, sanitise_evidence


@override_settings(MAX_IMPORT_FILE_SIZE_BYTES=5 * 1024 * 1024)
class NmapParserTests(TestCase):
    def setUp(self):
        self.importer = NmapXmlImporter(max_size_bytes=5 * 1024 * 1024)

    def sample_content(self):
        with open("fixtures/nmap/sample.xml", "rb") as fixture:
            return fixture.read()

    def test_valid_fixture_parses_open_ports_and_nse_script(self):
        observations = self.importer.parse(self.sample_content())

        self.assertEqual(len(observations), 3)
        port_observations = [item for item in observations if item.scanner_plugin_id == "nmap-port"]
        script_observations = [item for item in observations if item.scanner_plugin_id == "ssl-enum-ciphers"]
        self.assertEqual(len(port_observations), 2)
        self.assertEqual(len(script_observations), 1)
        self.assertTrue(any(item.title.startswith("Open TCP/443") for item in port_observations))
        self.assertEqual(script_observations[0].title, "Nmap NSE: ssl-enum-ciphers")

    def test_open_port_uses_nmap_port_plugin_id(self):
        observations = self.importer.parse(self.sample_content())

        open_443 = next(item for item in observations if item.port == 443 and item.scanner_plugin_id == "nmap-port")
        self.assertEqual(open_443.scanner_plugin_id, "nmap-port")
        self.assertEqual(open_443.raw_location, "192.0.2.10:443/tcp")

    def test_blank_wrong_extension_and_malformed_xml_fail_safely(self):
        cases = [
            (b"", "sample.xml"),
            (self.sample_content(), "sample.txt"),
            (b"<nmaprun><host>", "sample.xml"),
        ]

        for content, filename in cases:
            with self.subTest(filename=filename, content=content[:12]):
                with self.assertRaises(ImportValidationError) as raised:
                    self.importer.validate(content, filename)
                self.assertNotIn("Traceback", str(raised.exception))
                self.assertNotIn("<host>", str(raised.exception))

    def test_doctype_or_entity_xml_is_rejected(self):
        unsafe = b'''<?xml version="1.0"?>
<!DOCTYPE foo [ <!ENTITY xxe SYSTEM "file:///etc/passwd"> ]>
<nmaprun>&xxe;</nmaprun>'''

        with self.assertRaises(ImportValidationError):
            self.importer.validate(unsafe, "sample.xml")

    def test_evidence_is_sanitised_and_truncated(self):
        value = "line\x00 one\n\n" + ("A" * 2500)

        cleaned = sanitise_evidence(value, max_length=80)

        self.assertNotIn("\x00", cleaned)
        self.assertNotIn("\n", cleaned)
        self.assertTrue(cleaned.endswith("... [truncated]"))
        self.assertLessEqual(len(cleaned), 80)

    def test_parser_does_not_persist_database_records(self):
        self.importer.validate(self.sample_content(), "sample.xml")
        self.importer.parse(self.sample_content())

        self.assertEqual(ScanImport.objects.count(), 0)
        self.assertEqual(ScannerObservation.objects.count(), 0)
