from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.assessments.models import Asset
from apps.findings.models import Finding
from apps.imports.tests.helpers import ImportTestDataMixin


class FindingLifecycleTests(ImportTestDataMixin, TestCase):
    def setUp(self):
        self.api = APIClient()
        self.create_import_domain()
        self.asset = Asset.objects.create(
            assessment=self.assessment_a,
            asset_type=Asset.AssetType.APPLICATION,
            display_name="Northwind Portal",
            base_url="https://portal.northwind.example",
            environment=Asset.Environment.PRODUCTION,
            criticality=Asset.Criticality.HIGH,
            internet_exposed=True,
        )
        self.finding = Finding.objects.create(
            assessment=self.assessment_a,
            affected_asset=self.asset,
            title="Lifecycle finding",
            description="Fictional description.",
            cvss_score="7.5",
            business_impact="Fictional impact.",
            remediation="Fictional remediation.",
            remediation_owner="Web Team",
            due_date=timezone.localdate() + timedelta(days=10),
            created_by=self.consultant_a,
        )

    def patch(self, user, payload):
        self.api.force_authenticate(user)
        return self.api.patch(reverse("finding-detail", args=[self.finding.id]), payload, format="json")

    def test_consultant_updates_lifecycle_fields_and_audit_events(self):
        response = self.patch(self.consultant_a, {
            "status": Finding.Status.IN_PROGRESS,
            "remediation_owner": "Platform Team",
            "due_date": (timezone.localdate() + timedelta(days=20)).isoformat(),
            "business_impact": "Updated fictional impact.",
            "remediation": "Updated fictional remediation.",
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.finding.refresh_from_db()
        self.assertEqual(self.finding.status, Finding.Status.IN_PROGRESS)
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.FINDING_STATUS_CHANGED, entity_id=self.finding.id).exists())
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.FINDING_OWNER_CHANGED, entity_id=self.finding.id).exists())
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.FINDING_DUE_DATE_CHANGED, entity_id=self.finding.id).exists())

    def test_manager_and_client_cannot_update_finding(self):
        manager_response = self.patch(self.manager_a, {"status": Finding.Status.IN_PROGRESS})
        client_response = self.patch(self.client_user_a, {"status": Finding.Status.IN_PROGRESS})

        self.assertEqual(manager_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(client_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unassigned_consultant_cannot_update_other_client_finding(self):
        response = self.patch(self.consultant_b, {"status": Finding.Status.IN_PROGRESS})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_closed_requires_validation_evidence_and_sets_validator(self):
        missing = self.patch(self.consultant_a, {"status": Finding.Status.CLOSED})
        ok = self.patch(self.consultant_a, {
            "status": Finding.Status.CLOSED,
            "validation_evidence": "Validated fixed version and authorised retest on 2026-07-20.",
        })

        self.assertEqual(missing.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ok.status_code, status.HTTP_200_OK)
        self.finding.refresh_from_db()
        self.assertEqual(self.finding.validated_by, self.consultant_a)
        self.assertIsNotNone(self.finding.validated_at)
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.FINDING_CLOSED, entity_id=self.finding.id).exists())

    def test_accepted_risk_requires_reason_and_future_review_date(self):
        missing_reason = self.patch(self.consultant_a, {
            "status": Finding.Status.ACCEPTED_RISK,
            "risk_review_due_date": (timezone.localdate() + timedelta(days=30)).isoformat(),
        })
        past_date = self.patch(self.consultant_a, {
            "status": Finding.Status.ACCEPTED_RISK,
            "risk_acceptance_reason": "Legacy system retirement is scheduled.",
            "risk_review_due_date": (timezone.localdate() - timedelta(days=1)).isoformat(),
        })
        ok = self.patch(self.consultant_a, {
            "status": Finding.Status.ACCEPTED_RISK,
            "risk_acceptance_reason": "Legacy system retirement is scheduled.",
            "risk_review_due_date": (timezone.localdate() + timedelta(days=30)).isoformat(),
        })

        self.assertEqual(missing_reason.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(past_date.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ok.status_code, status.HTTP_200_OK)
        self.finding.refresh_from_db()
        self.assertEqual(self.finding.risk_accepted_by, self.consultant_a)
        self.assertIsNotNone(self.finding.risk_accepted_at)
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.FINDING_RISK_ACCEPTED, entity_id=self.finding.id).exists())

    def test_reopening_terminal_status_creates_audit_event_and_keeps_acceptance_history(self):
        self.patch(self.consultant_a, {
            "status": Finding.Status.ACCEPTED_RISK,
            "risk_acceptance_reason": "Legacy system retirement is scheduled.",
            "risk_review_due_date": (timezone.localdate() + timedelta(days=30)).isoformat(),
        })
        reopened = self.patch(self.consultant_a, {"status": Finding.Status.IN_PROGRESS})

        self.assertEqual(reopened.status_code, status.HTTP_200_OK)
        self.finding.refresh_from_db()
        self.assertEqual(self.finding.status, Finding.Status.IN_PROGRESS)
        self.assertTrue(self.finding.risk_acceptance_reason)
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.FINDING_REOPENED, entity_id=self.finding.id).exists())

    def test_lifecycle_patch_does_not_allow_severity_override(self):
        response = self.patch(self.consultant_a, {"status": Finding.Status.IN_PROGRESS, "severity": Finding.Severity.CRITICAL})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.finding.refresh_from_db()
        self.assertEqual(self.finding.severity, Finding.derive_severity(self.finding.cvss_score))

    def test_audit_timeline_permissions(self):
        self.patch(self.consultant_a, {"status": Finding.Status.IN_PROGRESS})

        self.api.force_authenticate(self.consultant_a)
        consultant = self.api.get(reverse("finding-audit-logs", args=[self.finding.id]))
        self.api.force_authenticate(self.manager_a)
        manager = self.api.get(reverse("finding-audit-logs", args=[self.finding.id]))
        self.api.force_authenticate(self.client_user_a)
        client = self.api.get(reverse("finding-audit-logs", args=[self.finding.id]))
        self.api.force_authenticate(self.consultant_b)
        hidden = self.api.get(reverse("finding-audit-logs", args=[self.finding.id]))

        self.assertEqual(consultant.status_code, status.HTTP_200_OK)
        self.assertEqual(manager.status_code, status.HTTP_200_OK)
        self.assertEqual(client.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(hidden.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("safe_metadata", consultant.json()["results"][0])
