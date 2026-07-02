from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.assessments.models import Asset, Assessment
from apps.findings.models import Finding
from apps.tenancy.models import Client, ClientMembership


class TenantScopedAccessControlTests(TestCase):
    def setUp(self):
        self.api = APIClient()
        User = get_user_model()
        self.admin = User.objects.create_user(
            email="admin@example.test",
            password="test-pass-12345",
            role=User.Role.ADMIN,
        )
        self.consultant_a = User.objects.create_user(
            email="consultant-a@example.test",
            password="test-pass-12345",
            role=User.Role.CONSULTANT,
        )
        self.consultant_b = User.objects.create_user(
            email="consultant-b@example.test",
            password="test-pass-12345",
            role=User.Role.CONSULTANT,
        )
        self.manager_a = User.objects.create_user(
            email="manager-a@example.test",
            password="test-pass-12345",
            role=User.Role.MANAGER,
        )
        self.client_user_a = User.objects.create_user(
            email="client-a@example.test",
            password="test-pass-12345",
            role=User.Role.CLIENT,
        )

        self.client_a = Client.objects.create(
            name="Northwind Healthcare",
            industry="Healthcare",
            contact_name="Nora North",
            contact_email="nora@example.test",
        )
        self.client_b = Client.objects.create(
            name="Contoso Manufacturing",
            industry="Manufacturing",
            contact_name="Connie Contoso",
            contact_email="connie@example.test",
        )

        ClientMembership.objects.create(
            user=self.consultant_a,
            client=self.client_a,
            relationship_role=ClientMembership.RelationshipRole.CONSULTANT,
        )
        ClientMembership.objects.create(
            user=self.consultant_b,
            client=self.client_b,
            relationship_role=ClientMembership.RelationshipRole.CONSULTANT,
        )
        ClientMembership.objects.create(
            user=self.manager_a,
            client=self.client_a,
            relationship_role=ClientMembership.RelationshipRole.MANAGER,
        )
        ClientMembership.objects.create(
            user=self.client_user_a,
            client=self.client_a,
            relationship_role=ClientMembership.RelationshipRole.CLIENT_USER,
        )

        self.assessment_a = self.create_assessment(self.client_a, self.consultant_a, "Northwind Review")
        self.assessment_b = self.create_assessment(self.client_b, self.consultant_b, "Contoso Review")
        self.asset_a = self.create_asset(self.assessment_a, "Northwind Portal")
        self.asset_b = self.create_asset(self.assessment_b, "Contoso ERP")
        self.finding_a = self.create_finding(self.assessment_a, self.asset_a, self.consultant_a, "Northwind Finding")
        self.finding_b = self.create_finding(self.assessment_b, self.asset_b, self.consultant_b, "Contoso Finding")

    def create_assessment(self, client, creator, name):
        return Assessment.objects.create(
            client=client,
            name=name,
            framework=Assessment.Framework.OWASP,
            status=Assessment.Status.ACTIVE,
            start_date=date(2026, 7, 1),
            scope_summary=f"Fictional scope for {name}.",
            created_by=creator,
        )

    def create_asset(self, assessment, display_name):
        return Asset.objects.create(
            assessment=assessment,
            asset_type=Asset.AssetType.APPLICATION,
            display_name=display_name,
            base_url=f"https://{display_name.lower().replace(' ', '-')}.example",
            environment=Asset.Environment.PRODUCTION,
            criticality=Asset.Criticality.HIGH,
            internet_exposed=True,
        )

    def create_finding(self, assessment, asset, creator, title):
        return Finding.objects.create(
            assessment=assessment,
            affected_asset=asset,
            title=title,
            description="A fictional confirmed finding.",
            cvss_score="7.0",
            business_impact="Potential business impact for demonstration.",
            remediation="Apply a reviewed remediation plan.",
            remediation_owner="Platform Team",
            status=Finding.Status.OPEN,
            created_by=creator,
        )

    def assessment_payload(self, client_id=None):
        return {
            "client": client_id or self.client_a.id,
            "name": "New Assessment",
            "framework": Assessment.Framework.OWASP,
            "status": Assessment.Status.PLANNED,
            "start_date": "2026-07-05",
            "end_date": None,
            "scope_summary": "A fictional authorised assessment.",
        }

    def asset_payload(self, assessment_id=None):
        return {
            "assessment": assessment_id or self.assessment_a.id,
            "asset_type": Asset.AssetType.HOST,
            "display_name": "New Host",
            "hostname": "new-host.example.test",
            "ip_address": None,
            "base_url": "",
            "environment": Asset.Environment.PRODUCTION,
            "criticality": Asset.Criticality.MEDIUM,
            "internet_exposed": False,
            "owner": "Infrastructure Team",
        }

    def finding_payload(self, assessment_id=None, asset_id=None):
        return {
            "assessment": assessment_id or self.assessment_a.id,
            "affected_asset": asset_id or self.asset_a.id,
            "title": "New Finding",
            "description": "A fictional confirmed issue.",
            "cve_id": "",
            "cvss_score": "5.0",
            "business_impact": "Could affect a fictional service.",
            "remediation": "Apply a controlled remediation.",
            "remediation_owner": "Application Team",
            "status": Finding.Status.OPEN,
            "due_date": "2026-08-01",
        }

    def results(self, response):
        return response.json()["results"]

    def test_unauthenticated_request_is_denied(self):
        response = self.api.get(reverse("client-list"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_consultant_lists_only_assigned_client_records(self):
        self.api.force_authenticate(self.consultant_a)

        client_response = self.api.get(reverse("client-list"))
        assessment_response = self.api.get(reverse("assessment-list"))
        asset_response = self.api.get(reverse("asset-list"))
        finding_response = self.api.get(reverse("finding-list"))

        self.assertEqual([item["id"] for item in self.results(client_response)], [self.client_a.id])
        self.assertEqual([item["id"] for item in self.results(assessment_response)], [self.assessment_a.id])
        self.assertEqual([item["id"] for item in self.results(asset_response)], [self.asset_a.id])
        self.assertEqual([item["id"] for item in self.results(finding_response)], [self.finding_a.id])

    def test_consultant_cannot_retrieve_or_update_other_client_records(self):
        self.api.force_authenticate(self.consultant_a)

        for route_name, obj in [
            ("assessment-detail", self.assessment_b),
            ("asset-detail", self.asset_b),
            ("finding-detail", self.finding_b),
        ]:
            with self.subTest(route_name=route_name):
                detail_url = reverse(route_name, args=[obj.id])
                self.assertEqual(self.api.get(detail_url).status_code, status.HTTP_404_NOT_FOUND)
                self.assertEqual(
                    self.api.patch(detail_url, {"status": "ARCHIVED"}, format="json").status_code,
                    status.HTTP_404_NOT_FOUND,
                )

    def test_admin_can_access_both_client_records(self):
        self.api.force_authenticate(self.admin)

        client_response = self.api.get(reverse("client-list"))
        assessment_response = self.api.get(reverse("assessment-list"))

        self.assertEqual({item["id"] for item in self.results(client_response)}, {self.client_a.id, self.client_b.id})
        self.assertEqual(
            {item["id"] for item in self.results(assessment_response)},
            {self.assessment_a.id, self.assessment_b.id},
        )

    def test_admin_can_create_client(self):
        self.api.force_authenticate(self.admin)

        response = self.api.post(
            reverse("client-list"),
            {
                "name": "Fabrikam Finance",
                "industry": "Financial services",
                "contact_name": "Frank Fabrikam",
                "contact_email": "frank@example.test",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_consultant_cannot_create_client(self):
        self.api.force_authenticate(self.consultant_a)

        response = self.api.post(
            reverse("client-list"),
            {
                "name": "Fabrikam Finance",
                "industry": "Financial services",
                "contact_name": "Frank Fabrikam",
                "contact_email": "frank@example.test",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_assigned_consultant_can_create_assessment_asset_and_finding(self):
        self.api.force_authenticate(self.consultant_a)

        assessment_response = self.api.post(
            reverse("assessment-list"),
            self.assessment_payload(),
            format="json",
        )
        self.assertEqual(assessment_response.status_code, status.HTTP_201_CREATED)

        asset_response = self.api.post(
            reverse("asset-list"),
            self.asset_payload(assessment_id=assessment_response.json()["id"]),
            format="json",
        )
        self.assertEqual(asset_response.status_code, status.HTTP_201_CREATED)

        finding_response = self.api.post(
            reverse("finding-list"),
            self.finding_payload(
                assessment_id=assessment_response.json()["id"],
                asset_id=asset_response.json()["id"],
            ),
            format="json",
        )
        self.assertEqual(finding_response.status_code, status.HTTP_201_CREATED)

    def test_unassigned_consultant_cannot_create_records_for_other_client(self):
        self.api.force_authenticate(self.consultant_a)

        assessment_response = self.api.post(
            reverse("assessment-list"),
            self.assessment_payload(client_id=self.client_b.id),
            format="json",
        )
        asset_response = self.api.post(
            reverse("asset-list"),
            self.asset_payload(assessment_id=self.assessment_b.id),
            format="json",
        )
        finding_response = self.api.post(
            reverse("finding-list"),
            self.finding_payload(assessment_id=self.assessment_b.id, asset_id=self.asset_b.id),
            format="json",
        )

        self.assertEqual(assessment_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(asset_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(finding_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_can_read_but_cannot_create_or_update(self):
        self.api.force_authenticate(self.manager_a)

        self.assertEqual(
            self.api.get(reverse("assessment-detail", args=[self.assessment_a.id])).status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            self.api.post(reverse("assessment-list"), self.assessment_payload(), format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.api.patch(
                reverse("finding-detail", args=[self.finding_a.id]),
                {"status": Finding.Status.IN_PROGRESS},
                format="json",
            ).status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_client_user_can_read_own_client_only_and_cannot_write(self):
        self.api.force_authenticate(self.client_user_a)

        client_response = self.api.get(reverse("client-list"))
        self.assertEqual([item["id"] for item in self.results(client_response)], [self.client_a.id])
        self.assertEqual(
            self.api.get(reverse("assessment-detail", args=[self.assessment_b.id])).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            self.api.post(reverse("finding-list"), self.finding_payload(), format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )
