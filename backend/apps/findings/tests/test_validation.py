from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.assessments.models import Asset, Assessment
from apps.findings.models import Finding
from apps.tenancy.models import Client, ClientMembership


class FindingValidationTests(TestCase):
    def setUp(self):
        self.api = APIClient()
        self.user = get_user_model().objects.create_user(
            email="consultant-a@example.test",
            password="test-pass-12345",
            role=get_user_model().Role.CONSULTANT,
        )
        self.client_record = Client.objects.create(
            name="Northwind Healthcare",
            industry="Healthcare",
            contact_name="Nora North",
            contact_email="nora@example.test",
        )
        ClientMembership.objects.create(
            user=self.user,
            client=self.client_record,
            relationship_role=ClientMembership.RelationshipRole.CONSULTANT,
        )
        self.assessment = Assessment.objects.create(
            client=self.client_record,
            name="Northwind External Review",
            framework=Assessment.Framework.OWASP,
            status=Assessment.Status.ACTIVE,
            start_date=date(2026, 7, 1),
            scope_summary="Fictional external review scope.",
            created_by=self.user,
        )
        self.asset = Asset.objects.create(
            assessment=self.assessment,
            asset_type=Asset.AssetType.APPLICATION,
            display_name="Northwind Portal",
            base_url="https://portal.northwind.example",
            environment=Asset.Environment.PRODUCTION,
            criticality=Asset.Criticality.HIGH,
            internet_exposed=True,
        )
        self.api.force_authenticate(self.user)

    def finding_payload(self, cvss_score="4.0", **overrides):
        payload = {
            "assessment": self.assessment.id,
            "affected_asset": self.asset.id,
            "title": "Missing security header",
            "description": "A fictional scanner observation was confirmed by a consultant.",
            "cve_id": "",
            "cvss_score": cvss_score,
            "business_impact": "Could increase browser-side attack impact.",
            "remediation": "Add the missing response header after review.",
            "remediation_owner": "Platform Team",
            "status": Finding.Status.OPEN,
            "due_date": "2026-08-01",
        }
        payload.update(overrides)
        return payload

    def test_cvss_boundaries_derive_expected_severity(self):
        cases = {
            Decimal("0.0"): Finding.Severity.INFORMATIONAL,
            Decimal("0.1"): Finding.Severity.LOW,
            Decimal("3.9"): Finding.Severity.LOW,
            Decimal("4.0"): Finding.Severity.MEDIUM,
            Decimal("6.9"): Finding.Severity.MEDIUM,
            Decimal("7.0"): Finding.Severity.HIGH,
            Decimal("8.9"): Finding.Severity.HIGH,
            Decimal("9.0"): Finding.Severity.CRITICAL,
            Decimal("10.0"): Finding.Severity.CRITICAL,
        }

        for score, expected in cases.items():
            with self.subTest(score=score):
                self.assertEqual(Finding.derive_severity(score), expected)

    def test_cvss_zero_and_ten_are_accepted(self):
        for score in ["0.0", "10.0"]:
            with self.subTest(score=score):
                response = self.api.post(
                    reverse("finding-list"),
                    self.finding_payload(cvss_score=score, title=f"Boundary {score}"),
                    format="json",
                )
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_invalid_cvss_values_are_rejected(self):
        for score in ["-0.1", "10.1"]:
            with self.subTest(score=score):
                response = self.api.post(
                    reverse("finding-list"),
                    self.finding_payload(cvss_score=score),
                    format="json",
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("cvss_score", response.json())

    def test_client_supplied_severity_cannot_override_derived_value(self):
        response = self.api.post(
            reverse("finding-list"),
            self.finding_payload(cvss_score="4.0", severity=Finding.Severity.CRITICAL),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["severity"], Finding.Severity.MEDIUM)
