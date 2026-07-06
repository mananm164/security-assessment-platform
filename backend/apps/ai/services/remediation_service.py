from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import APIException, ValidationError

from apps.ai.models import AIArtifact, AIArtifactSource
from apps.audit.models import AuditLog
from apps.audit.services import record_audit_event
from apps.ai.providers.factory import get_ai_provider
from .retrieval_service import RetrievalService


def safe_finding_context(finding) -> dict:
    source_summaries = []
    for source in finding.sources.select_related("scanner_observation").all()[:3]:
        observation = source.scanner_observation
        source_summaries.append({
            "source_tool": observation.source_tool,
            "title": observation.title[:255],
            "summary": observation.evidence_summary[:500],
        })
    asset = finding.affected_asset
    return {
        "title": finding.title[:255],
        "description": finding.description[:1000],
        "cve_id": finding.cve_id,
        "cvss_score": str(finding.cvss_score),
        "severity": finding.severity,
        "status": finding.status,
        "affected_asset_type": asset.asset_type if asset else "",
        "affected_asset_criticality": asset.criticality if asset else "",
        "internet_exposed": bool(asset and asset.internet_exposed),
        "safe_scanner_summaries": source_summaries,
    }


class RemediationService:
    prompt_version = "remediation-v1"

    def __init__(self, *, retrieval_service=None, ai_provider=None):
        self.retrieval_service = retrieval_service or RetrievalService()
        self.ai_provider = ai_provider or get_ai_provider()

    @transaction.atomic
    def generate(self, *, finding, actor) -> AIArtifact:
        context = safe_finding_context(finding)
        query = " ".join(str(value) for value in [
            context["title"], context["description"], context["cve_id"], context["affected_asset_type"], finding.remediation,
        ] if value)
        chunks = self.retrieval_service.retrieve(query, limit=3)
        if not chunks:
            raise ValidationError("No active knowledge base guidance is available for remediation drafting.")
        sources = [
            {
                "title": chunk.document.title,
                "source_name": chunk.document.source_name,
                "source_url": chunk.document.source_url,
                "category": chunk.document.category,
                "content": chunk.content[:1000],
            }
            for chunk in chunks
        ]
        try:
            content = self.ai_provider.generate_remediation(finding_context=context, sources=sources)
        except Exception as exc:
            raise APIException("AI provider unavailable; remediation draft was not created.") from exc
        if "Draft — human review required" not in content:
            content = "Draft — human review required\n\n" + content
        artifact = AIArtifact.objects.create(
            finding=finding,
            artifact_type=AIArtifact.ArtifactType.REMEDIATION,
            provider=getattr(self.ai_provider, "provider_name", "unknown"),
            model=getattr(self.ai_provider, "model", "unknown"),
            prompt_version=self.prompt_version,
            content=content,
            created_by=actor,
        )
        for rank, chunk in enumerate(chunks, start=1):
            distance = getattr(chunk, "distance", None)
            similarity = None
            if distance is not None:
                similarity = Decimal(str(max(0.0, 1.0 - float(distance)))).quantize(Decimal("0.00001"))
            AIArtifactSource.objects.create(
                artifact=artifact,
                knowledge_chunk=chunk,
                rank=rank,
                similarity=similarity,
                excerpt=chunk.content[:500],
            )
        record_audit_event(
            actor=actor,
            client=finding.assessment.client,
            assessment=finding.assessment,
            action=AuditLog.Action.AI_REMEDIATION_DRAFT_GENERATED,
            entity_type="FINDING",
            entity_id=finding.id,
            summary="AI remediation draft generated.",
            safe_metadata={
                "provider": artifact.provider,
                "model": artifact.model,
                "artifact_id": artifact.id,
            },
        )
        return artifact
