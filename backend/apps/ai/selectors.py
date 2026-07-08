from apps.ai.models import AIArtifact
from apps.findings.selectors import visible_findings_for


def visible_ai_artifacts_for(user):
    return (
        AIArtifact.objects.filter(finding__in=visible_findings_for(user))
        .select_related("finding", "created_by")
        .prefetch_related("sources__knowledge_chunk__document")
    )
