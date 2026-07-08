from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.assessments.models import Asset, Assessment
from apps.findings.models import Finding
from apps.tenancy.models import Client, ClientMembership


class Command(BaseCommand):
    help = "Seed fictional browser E2E data. Refuses to run outside E2E_TEST_MODE=1."

    @transaction.atomic
    def handle(self, *args, **options):
        if getattr(settings, "E2E_TEST_MODE", "") != "1":
            raise CommandError("seed_e2e_data may only run when E2E_TEST_MODE=1.")

        password = getattr(settings, "E2E_TEST_PASSWORD", "")
        if not password or password == "change-me-e2e-only":  # pragma: allowlist secret
            raise CommandError("E2E_TEST_PASSWORD must be set to a test-only value in the environment.")

        User = get_user_model()
        consultant = self._user(User, "consultant.e2e@sarp.example", User.Role.CONSULTANT, password)
        client_user = self._user(User, "client.e2e@sarp.example", User.Role.CLIENT, password)

        client, _ = Client.objects.update_or_create(
            name="E2E Northwind Fictional Client",
            defaults={
                "industry": "Healthcare",
                "contact_name": "Eve Example",
                "contact_email": "northwind-contact@sarp.example",
            },
        )
        ClientMembership.objects.update_or_create(
            user=consultant,
            client=client,
            defaults={
                "relationship_role": ClientMembership.RelationshipRole.CONSULTANT,
                "is_active": True,
            },
        )
        ClientMembership.objects.update_or_create(
            user=client_user,
            client=client,
            defaults={
                "relationship_role": ClientMembership.RelationshipRole.CLIENT_USER,
                "is_active": True,
            },
        )

        assessment, _ = Assessment.objects.update_or_create(
            client=client,
            name="E2E Northwind Browser Import",
            defaults={
                "framework": Assessment.Framework.OWASP,
                "status": Assessment.Status.ACTIVE,
                "start_date": date(2026, 7, 7),
                "scope_summary": "Fictional E2E assessment for local browser tests only.",
                "created_by": consultant,
            },
        )
        asset, _ = Asset.objects.update_or_create(
            assessment=assessment,
            display_name="E2E training portal",
            defaults={
                "asset_type": Asset.AssetType.APPLICATION,
                "hostname": "portal.e2e.sarp.example",
                "base_url": "https://portal.e2e.sarp.example",
                "environment": Asset.Environment.TEST,
                "criticality": Asset.Criticality.MEDIUM,
                "internet_exposed": False,
                "owner": "E2E Platform Team",
            },
        )
        Finding.objects.update_or_create(
            assessment=assessment,
            title="E2E approved fictional finding",
            defaults={
                "affected_asset": asset,
                "description": "Fictional client-visible finding for E2E visibility checks.",
                "cvss_score": Decimal("4.2"),
                "business_impact": "Fictional business impact for UI testing.",
                "remediation": "Apply the fictional remediation outside SARP.",
                "remediation_owner": "E2E Platform Team",
                "status": Finding.Status.OPEN,
                "due_date": timezone.localdate() + timedelta(days=14),
                "created_by": consultant,
            },
        )

        self.stdout.write(self.style.SUCCESS("Seeded fictional E2E users, client, assessment and finding."))

    def _user(self, User, email: str, role: str, password: str):
        if not email.endswith("@sarp.example"):
            raise CommandError("E2E users must use @sarp.example addresses.")
        user, _ = User.objects.update_or_create(
            email=email,
            defaults={
                "role": role,
                "is_active": True,
                "is_staff": False,
                "is_superuser": False,
            },
        )
        user.set_password(password)
        user.save(update_fields=["password", "role", "is_active", "is_staff", "is_superuser"])
        return user
