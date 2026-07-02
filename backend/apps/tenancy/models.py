from django.conf import settings
from django.db import models


class Client(models.Model):
    name = models.CharField(max_length=255, unique=True)
    industry = models.CharField(max_length=120)
    contact_name = models.CharField(max_length=255)
    contact_email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class ClientMembership(models.Model):
    class RelationshipRole(models.TextChoices):
        CONSULTANT = "CONSULTANT", "Consultant"
        MANAGER = "MANAGER", "Manager"
        CLIENT_USER = "CLIENT_USER", "Client user"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="client_memberships",
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    relationship_role = models.CharField(
        max_length=20,
        choices=RelationshipRole.choices,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "client"],
                name="unique_user_client_membership",
            )
        ]
        ordering = ["client__name", "user__email"]

    def __str__(self) -> str:
        return f"{self.user} -> {self.client}"
