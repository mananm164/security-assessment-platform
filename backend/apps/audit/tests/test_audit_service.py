from django.test import TestCase

from apps.audit.models import AuditLog
from apps.audit.services import record_audit_event, safe_metadata
from apps.imports.tests.helpers import ImportTestDataMixin


class AuditServiceTests(ImportTestDataMixin, TestCase):
    def setUp(self):
        self.create_import_domain()

    def test_record_audit_event_persists_only_safe_metadata(self):
        log = record_audit_event(
            actor=self.consultant_a,
            client=self.client_a,
            assessment=self.assessment_a,
            action=AuditLog.Action.FINDING_STATUS_CHANGED,
            entity_type="FINDING",
            entity_id=123,
            safe_metadata={
                "old_status": "OPEN",
                "new_status": "IN_PROGRESS",
                "password": "secret",
                "raw_report": "<xml>secret</xml>",
                "source_filename": "scan.xml",
            },
        )

        self.assertEqual(log.safe_metadata["old_status"], "OPEN")
        self.assertEqual(log.safe_metadata["source_filename"], "scan.xml")
        self.assertNotIn("password", log.safe_metadata)
        self.assertNotIn("raw_report", log.safe_metadata)
        self.assertEqual(log.metadata, log.safe_metadata)

    def test_safe_metadata_redacts_sensitive_string_values(self):
        cleaned = safe_metadata({"source_filename": "token=abc123", "new_status": "CLOSED"})

        self.assertEqual(cleaned["source_filename"], "[redacted]")
        self.assertEqual(cleaned["new_status"], "CLOSED")
