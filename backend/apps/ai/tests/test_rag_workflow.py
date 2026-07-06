from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.ai.models import AIArtifact, KnowledgeChunk, KnowledgeDocument
from apps.ai.providers.mock_embeddings import MockEmbeddingProvider
from apps.ai.services.knowledge_ingestion_service import KnowledgeIngestionService
from apps.ai.services.remediation_service import RemediationService, safe_finding_context
from apps.ai.services.retrieval_service import RetrievalService
from apps.assessments.models import Asset
from apps.audit.models import AuditLog
from apps.findings.models import Finding
from apps.imports.tests.helpers import ImportTestDataMixin


class KnowledgeIngestionTests(TestCase):

    def test_initial_migration_enables_pgvector_extension(self):
        migration = Path("apps/ai/migrations/0001_initial.py").read_text(encoding="utf-8")

        self.assertIn("VectorExtension()", migration)
        self.assertLess(migration.index("VectorExtension()"), migration.index("KnowledgeChunk"))

    def test_mock_embeddings_have_locked_dimension(self):
        vector = MockEmbeddingProvider().embed(["access control"])[0]

        self.assertEqual(len(vector), 768)

    def test_ingestion_is_idempotent_and_writes_vectors(self):
        directory = Path("knowledge_base")
        service = KnowledgeIngestionService(embedding_provider=MockEmbeddingProvider())

        first = service.ingest_directory(directory)
        second = service.ingest_directory(directory)

        self.assertEqual(first["documents_seen"], 6)
        self.assertEqual(first["chunks_written"], 6)
        self.assertEqual(second["chunks_written"], 0)
        self.assertEqual(KnowledgeDocument.objects.count(), 6)
        self.assertEqual(len(KnowledgeChunk.objects.first().embedding), 768)

    def test_management_command_ingests_knowledge_base(self):
        call_command("ingest_knowledge_base", directory="knowledge_base", verbosity=0)

        self.assertEqual(KnowledgeDocument.objects.count(), 6)


@override_settings(AI_PROVIDER="mock", EMBEDDING_PROVIDER="mock", EMBEDDING_DIMENSIONS=768)
class RemediationWorkflowTests(ImportTestDataMixin, TestCase):
    def setUp(self):
        self.api = APIClient()
        self.create_import_domain()
        self.asset = Asset.objects.create(
            assessment=self.assessment_a,
            asset_type=Asset.AssetType.APPLICATION,
            display_name="Northwind Portal",
            base_url="https://portal.northwind.example",
            environment=Asset.Environment.PRODUCTION,
            criticality=Asset.Criticality.HIGH,
            internet_exposed=True,
        )
        self.finding = Finding.objects.create(
            assessment=self.assessment_a,
            affected_asset=self.asset,
            title="Access control bypass",
            description="Fictional BOLA issue permits access to another tenant record.",
            cve_id="CVE-2024-1234",
            cvss_score="8.0",
            business_impact="Fictional tenant data exposure.",
            remediation="Fix authorization and add tests.",
            remediation_owner="Platform Team",
            created_by=self.consultant_a,
        )
        KnowledgeIngestionService(embedding_provider=MockEmbeddingProvider()).ingest_directory(Path("knowledge_base"))

    def test_retrieval_returns_relevant_access_control_chunk(self):
        chunks = RetrievalService(embedding_provider=MockEmbeddingProvider()).retrieve("access control tenant authorization", limit=3)

        self.assertEqual(chunks[0].document.category, "access_control")

    def test_remediation_generation_persists_artifact_and_sources(self):
        artifact = RemediationService().generate(finding=self.finding, actor=self.consultant_a)

        self.assertIn("Draft — human review required", artifact.content)
        self.assertEqual(artifact.sources.count(), 3)
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.AI_REMEDIATION_DRAFT_GENERATED, entity_id=self.finding.id).exists())
        self.assertNotIn("prompt", artifact.content.lower())

    def test_safe_context_excludes_raw_unsafe_fields(self):
        context = safe_finding_context(self.finding)

        self.assertIn("title", context)
        self.assertNotIn("raw", " ".join(context.keys()).lower())
        self.assertNotIn("token", str(context).lower())

    def test_ai_api_permissions_and_read_scope(self):
        self.api.force_authenticate(self.consultant_a)
        created = self.api.post(reverse("finding-ai-remediation", args=[self.finding.id]), {}, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(created.json()["review_label"], "Draft — human review required")

        listed = self.api.get(reverse("finding-ai-artifacts", args=[self.finding.id]))
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual(len(listed.json()["items"]), 1)

        self.api.force_authenticate(self.manager_a)
        denied = self.api.post(reverse("finding-ai-remediation", args=[self.finding.id]), {}, format="json")
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)
        readable = self.api.get(reverse("finding-ai-artifacts", args=[self.finding.id]))
        self.assertEqual(readable.status_code, status.HTTP_200_OK)

        self.api.force_authenticate(self.consultant_b)
        hidden = self.api.get(reverse("finding-ai-artifacts", args=[self.finding.id]))
        self.assertEqual(hidden.status_code, status.HTTP_404_NOT_FOUND)

    def test_provider_failure_returns_safe_error_without_artifact(self):
        provider = Mock(generate_remediation=Mock(side_effect=RuntimeError("connection string password=secret")), provider_name="mock", model="mock")
        with self.assertRaisesMessage(Exception, "AI provider unavailable"):
            RemediationService(ai_provider=provider).generate(finding=self.finding, actor=self.consultant_a)

        self.assertEqual(AIArtifact.objects.count(), 0)
