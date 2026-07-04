from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.ai.services.knowledge_ingestion_service import KnowledgeIngestionService


class Command(BaseCommand):
    help = "Ingest source-attributed local knowledge base files into pgvector."

    def add_arguments(self, parser):
        parser.add_argument("--directory", default="knowledge_base")

    def handle(self, *args, **options):
        directory = Path(options["directory"])
        if not directory.is_absolute():
            directory = settings.BASE_DIR / directory
        if not directory.exists():
            raise CommandError(f"Knowledge base directory not found: {directory}")
        result = KnowledgeIngestionService().ingest_directory(directory)
        self.stdout.write(self.style.SUCCESS(
            f"Ingested {result['documents_seen']} documents; {result['documents_changed']} changed; {result['chunks_written']} chunks written."
        ))
