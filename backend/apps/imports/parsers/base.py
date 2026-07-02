from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class NormalisedObservation:
    source_tool: str
    external_id: str
    title: str
    raw_severity: str | None = None
    confidence: str | None = None
    asset_identifier: str | None = None
    hostname: str | None = None
    port: int | None = None
    protocol: str | None = None
    url: str | None = None
    description: str = ""
    evidence_summary: str = ""
    suggested_remediation: str | None = None
    cve_ids: list[str] = field(default_factory=list)
    cwe_ids: list[str] = field(default_factory=list)
    scanner_plugin_id: str | None = None
    references: list[str] = field(default_factory=list)
    raw_location: str | None = None
    candidate_cvss_score: str | None = None
    candidate_cvss_vector: str | None = None


class BaseImporter(ABC):
    source_tool: str

    @abstractmethod
    def validate(self, content: bytes, filename: str) -> None:
        """Raise a safe ImportValidationError for bad or unsupported input."""

    @abstractmethod
    def parse(self, content: bytes) -> list[NormalisedObservation]:
        """Return normalised values only. Never write to the database here."""
