from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.assessments.models import Assessment
from apps.common.exceptions import ImportValidationError
from apps.imports.services.import_service import import_report


class Command(BaseCommand):
    help = "Import an authorised scanner export into an existing assessment."

    def add_arguments(self, parser):
        parser.add_argument("--assessment-id", type=int, required=True)
        parser.add_argument("--tool", required=True)
        parser.add_argument("--file", required=True)
        parser.add_argument("--actor-email", required=True)

    def handle(self, *args, **options):
        actor_email = options["actor_email"]
        User = get_user_model()
        try:
            actor = User.objects.get(email=actor_email)
        except User.DoesNotExist as exc:
            raise CommandError("Import failed: actor email was not found.") from exc

        try:
            assessment = Assessment.objects.select_related("client").get(id=options["assessment_id"])
        except Assessment.DoesNotExist as exc:
            raise CommandError("Import failed: assessment was not found.") from exc

        file_path = Path(options["file"])
        if not file_path.is_file():
            raise CommandError("Import failed: report file was not found.")

        try:
            scan_import = import_report(
                assessment=assessment,
                actor=actor,
                tool=options["tool"],
                filename=file_path.name,
                content=file_path.read_bytes(),
            )
        except ImportValidationError as exc:
            raise CommandError(f"Import failed: {exc}") from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {scan_import.source_tool.title()} report into assessment {assessment.id}."
            )
        )
        self.stdout.write(f"Import ID: {scan_import.id}")
        self.stdout.write(f"Observations created: {scan_import.observations_created}")
        self.stdout.write(f"Observations re-observed: {scan_import.observations_updated}")
