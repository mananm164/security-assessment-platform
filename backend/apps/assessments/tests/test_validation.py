from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.assessments.models import Assessment
from apps.tenancy.models import Client, ClientMembership


class AssessmentAssetValidationTests(TestCase):
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
        self.api.force_authenticate(self.user)

    def test_assessment_end_date_before_start_date_is_rejected(self):
        response = self.api.post(
            reverse("assessment-list"),
            {
                "client": self.client_record.id,
                "name": "Invalid dates",
                "framework": Assessment.Framework.OWASP,
                "status": Assessment.Status.PLANNED,
                "start_date": "2026-07-10",
                "end_date": "2026-07-01",
                "scope_summary": "Dates should fail validation.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("end_date", response.json())

    def test_asset_without_useful_identifier_is_rejected(self):
        response = self.api.post(
            reverse("asset-list"),
            {
                "assessment": self.assessment.id,
                "asset_type": "HOST",
                "display_name": "",
                "hostname": "",
                "ip_address": None,
                "base_url": "",
                "environment": "PRODUCTION",
                "criticality": "HIGH",
                "internet_exposed": True,
                "owner": "",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
