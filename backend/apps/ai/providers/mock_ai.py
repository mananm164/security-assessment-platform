class MockAIProvider:
    provider_name = "mock"

    def __init__(self, *, model: str = "mock-remediation"):
        self.model = model

    def generate_remediation(self, *, finding_context: dict, sources: list[dict]) -> str:
        title = finding_context.get("title", "the finding")
        source_titles = ", ".join(source.get("title", "source") for source in sources) or "the curated guidance"
        return (
            "Draft — human review required\n\n"
            f"Executive summary\nReview and remediate {title} using the cited SARP guidance.\n\n"
            "Technical risk\nThe weakness may expose systems or data if left unresolved.\n\n"
            "Business impact\nPotential impact includes service disruption, data exposure, compliance concern, or delayed remediation assurance.\n\n"
            "Recommended remediation steps\n1. Confirm the affected component and owner.\n2. Apply the least disruptive corrective control.\n3. Document any compensating controls.\n\n"
            "Validation steps\nRetest the affected path, confirm monitoring coverage, and retain safe validation evidence.\n\n"
            f"Caveats and assumptions\nThis draft is grounded in: {source_titles}. Human review is required before use."
        )
