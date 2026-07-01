from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import User


class Command(BaseCommand):
    help = "Create or update the fictional Day 1 development consultant user."

    def handle(self, *args, **options):
        email = getattr(settings, "DEV_SEED_EMAIL", None)
        password = getattr(settings, "DEV_SEED_PASSWORD", None)

        if not email or not password:
            raise CommandError("DEV_SEED_EMAIL and DEV_SEED_PASSWORD must be configured.")

        user, created = User.objects.update_or_create(
            email=email,
            defaults={
                "role": User.Role.CONSULTANT,
                "is_active": True,
                "is_staff": False,
                "is_superuser": False,
            },
        )
        user.set_password(password)
        user.save(update_fields=["password", "role", "is_active", "is_staff", "is_superuser"])

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} development user {user.email} with role {user.role}."))
