from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.imports.models import ImportPreview


class Command(BaseCommand):
    help = "Delete expired, unconfirmed scanner import previews."

    def handle(self, *args, **options):
        deleted_count, _ = ImportPreview.objects.filter(
            confirmed_at__isnull=True,
            expires_at__lt=timezone.now(),
        ).delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted_count} expired import preview(s)."))
