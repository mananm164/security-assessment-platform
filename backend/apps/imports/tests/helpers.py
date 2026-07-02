from datetime import date
from pathlib import Path

from django.contrib.auth import get_user_model

from apps.assessments.models import Assessment
from apps.tenancy.models import Client, ClientMembership

FIXTURE_PATH = Path("fixtures/nmap/sample.xml")


class ImportTestDataMixin:
    def make_user(self, email, role):
        return get_user_model().objects.create_user(
            email=email,
            password="test-pass-12345",
            role=role,
        )

    def create_import_domain(self):
        User = get_user_model()
        self.admin = self.make_user("admin@example.test", User.Role.ADMIN)
        self.consultant_a = self.make_user("consultant-a@example.test", User.Role.CONSULTANT)
        self.consultant_b = self.make_user("consultant-b@example.test", User.Role.CONSULTANT)
        self.manager_a = self.make_user("manager-a@example.test", User.Role.MANAGER)
        self.client_user_a = self.make_user("client-a@example.test", User.Role.CLIENT)

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

        self.assessment_a = Assessment.objects.create(
            client=self.client_a,
            name="Northwind Import Review",
            framework=Assessment.Framework.OWASP,
            status=Assessment.Status.ACTIVE,
            start_date=date(2026, 7, 1),
            scope_summary="Fictional authorised Nmap import scope.",
            created_by=self.consultant_a,
        )
        self.assessment_b = Assessment.objects.create(
            client=self.client_b,
            name="Contoso Import Review",
            framework=Assessment.Framework.OWASP,
            status=Assessment.Status.ACTIVE,
            start_date=date(2026, 7, 1),
            scope_summary="Fictional authorised Nmap import scope.",
            created_by=self.consultant_b,
        )

    def sample_content(self):
        return FIXTURE_PATH.read_bytes()
