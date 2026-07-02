from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from apps.tenancy.models import Client, ClientMembership


class ClientMembershipModelTests(TestCase):
    def test_duplicate_user_client_membership_is_rejected(self):
        user = get_user_model().objects.create_user(
            email="consultant@example.test",
            password="test-pass-12345",
            role=get_user_model().Role.CONSULTANT,
        )
        client = Client.objects.create(
            name="Northwind Healthcare",
            industry="Healthcare",
            contact_name="Nora North",
            contact_email="nora@example.test",
        )
        ClientMembership.objects.create(
            user=user,
            client=client,
            relationship_role=ClientMembership.RelationshipRole.CONSULTANT,
        )

        with self.assertRaises(IntegrityError):
            ClientMembership.objects.create(
                user=user,
                client=client,
                relationship_role=ClientMembership.RelationshipRole.CONSULTANT,
            )
