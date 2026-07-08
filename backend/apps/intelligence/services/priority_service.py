from __future__ import annotations

from decimal import Decimal
from django.utils import timezone

from apps.assessments.models import Asset
from apps.findings.models import Finding
from apps.intelligence.models import VulnerabilityIntel


class PriorityService:
    @staticmethod
    def score(finding: Finding, intel: VulnerabilityIntel | None) -> dict:
        cvss_points = round(float(finding.cvss_score) * 6)
        kev_points = 25 if intel and intel.kev_listed else 0
        epss = Decimal(str(intel.epss_score)) if intel and intel.epss_score is not None else None
        if epss is None:
            epss_points = 0
        elif epss >= Decimal("0.70"):
            epss_points = 10
        elif epss >= Decimal("0.30"):
            epss_points = 7
        elif epss >= Decimal("0.10"):
            epss_points = 4
        else:
            epss_points = 0
        asset = finding.affected_asset
        if asset and asset.criticality == Asset.Criticality.CRITICAL:
            asset_points = 5
        elif asset and asset.criticality == Asset.Criticality.HIGH:
            asset_points = 3
        else:
            asset_points = 0
        exposure_points = 5 if asset and asset.internet_exposed else 0
        total = min(cvss_points + kev_points + epss_points + asset_points + exposure_points, 100)
        if total >= 85:
            label = "URGENT"
        elif total >= 65:
            label = "HIGH"
        elif total >= 35:
            label = "MEDIUM"
        else:
            label = "LOW"
        return {
            "cvss_points": cvss_points,
            "kev_points": kev_points,
            "epss_points": epss_points,
            "asset_criticality_points": asset_points,
            "internet_exposure_points": exposure_points,
            "total": total,
            "label": label,
        }

    @staticmethod
    def reason(finding: Finding, intel: VulnerabilityIntel | None, explanation: dict) -> str:
        parts = []
        if explanation["cvss_points"] >= 48:
            parts.append("a high CVSS score")
        elif explanation["cvss_points"] >= 30:
            parts.append("a moderate CVSS score")
        else:
            parts.append("a lower CVSS score")
        if intel and intel.kev_listed:
            parts.append("CISA KEV listing")
        if explanation["epss_points"] >= 10:
            parts.append("high EPSS likelihood")
        elif explanation["epss_points"] > 0:
            parts.append("elevated EPSS likelihood")
        if finding.affected_asset and finding.affected_asset.criticality in {
            Asset.Criticality.CRITICAL,
            Asset.Criticality.HIGH,
        }:
            parts.append(f"{finding.affected_asset.criticality.lower()} asset criticality")
        if finding.affected_asset and finding.affected_asset.internet_exposed:
            parts.append("internet exposure")
        joined = ", ".join(parts[:-1]) + (f", and {parts[-1]}" if len(parts) > 1 else parts[0])
        return f"{explanation['label'].title()} because the finding has {joined}."[:500]

    @classmethod
    def update_finding_priority(cls, finding: Finding, intel: VulnerabilityIntel | None) -> Finding:
        explanation = cls.score(finding, intel)
        finding.priority_score = explanation["total"]
        finding.priority_label = explanation["label"]
        finding.priority_explanation = explanation
        finding.priority_reason = cls.reason(finding, intel, explanation)
        finding.priority_computed_at = timezone.now()
        finding.save(
            update_fields=[
                "priority_score",
                "priority_label",
                "priority_explanation",
                "priority_reason",
                "priority_computed_at",
                "updated_at",
            ]
        )
        return finding
