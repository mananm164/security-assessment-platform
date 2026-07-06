from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.assessments.models import Asset
from apps.audit.models import AuditLog
from apps.findings.models import Finding
from apps.imports.tests.helpers import ImportTestDataMixin
from apps.intelligence.models import VulnerabilityIntel
from apps.intelligence.services.cisa_kev_client import CisaKevClient
from apps.intelligence.services.epss_client import EpssClient
from apps.intelligence.services.intelligence_service import IntelligenceService
from apps.intelligence.services.nvd_client import NvdClient, NvdResult
from apps.intelligence.services.priority_service import PriorityService


class IntelligenceClientParsingTests(TestCase):
    def test_nvd_parser_extracts_safe_fields(self):
        payload = {
            "vulnerabilities": [{"cve": {
                "descriptions": [{"lang": "en", "value": "Fictional CVE summary."}],
                "metrics": {"cvssMetricV31": [{"cvssData": {"baseScore": 8.8, "vectorString": "CVSS:3.1/AV:N"}}]},
                "weaknesses": [{"description": [{"value": "CWE-79"}]}],
                "references": {"referenceData": [{"url": "https://example.test/advisory", "source": "Vendor"}]},
            }}]
        }

        result = NvdClient.parse(payload)

        self.assertEqual(result.description, "Fictional CVE summary.")
        self.assertEqual(result.cvss_score, Decimal("8.8"))
        self.assertEqual(result.cwe_ids, ["CWE-79"])
        self.assertEqual(result.references[0]["title"], "Vendor")

    def test_cisa_and_epss_parsers_extract_values(self):
        kev = CisaKevClient.parse({"vulnerabilities": [{"cveID": "CVE-2024-1234", "dateAdded": "2026-01-02"}]}, "CVE-2024-1234")
        epss = EpssClient.parse({"data": [{"epss": "0.7400", "percentile": "0.9600"}]})

        self.assertTrue(kev.listed)
        self.assertEqual(kev.date_added, date(2026, 1, 2))
        self.assertEqual(epss.score, Decimal("0.7400"))
        self.assertEqual(epss.percentile, Decimal("0.9600"))


@override_settings(INTELLIGENCE_CACHE_TTL_HOURS=24)
class IntelligenceWorkflowTests(ImportTestDataMixin, TestCase):
    def setUp(self):
        self.api = APIClient()
        self.create_import_domain()
        self.asset = Asset.objects.create(
            assessment=self.assessment_a,
            asset_type=Asset.AssetType.APPLICATION,
            display_name="Northwind Portal",
            base_url="https://portal.northwind.example",
            environment=Asset.Environment.PRODUCTION,
            criticality=Asset.Criticality.CRITICAL,
            internet_exposed=True,
        )
        self.finding = Finding.objects.create(
            assessment=self.assessment_a,
            affected_asset=self.asset,
            title="Fictional access control CVE",
            description="A fictional vulnerable component has an access control weakness.",
            cve_id="cve-2024-1234",
            cvss_score="8.8",
            business_impact="Fictional impact.",
            remediation="Patch and validate access control.",
            remediation_owner="Platform Team",
            created_by=self.consultant_a,
        )

    def fake_service(self):
        return IntelligenceService(
            nvd_client=Mock(fetch=Mock(return_value=NvdResult("Summary", Decimal("8.8"), "CVSS", ["CWE-284"], []))),
            cisa_client=Mock(fetch=Mock(return_value=Mock(listed=True, date_added=date(2026, 1, 1)))),
            epss_client=Mock(fetch=Mock(return_value=Mock(score=Decimal("0.7400"), percentile=Decimal("0.9600")))),
        )

    def test_refresh_normalises_cve_and_updates_priority(self):
        result = self.fake_service().refresh_for_finding(self.finding)
        self.finding.refresh_from_db()

        self.assertFalse(result.used_cache)
        self.assertEqual(result.intel.cve_id, "CVE-2024-1234")
        self.assertEqual(self.finding.priority_score, 98)
        self.assertEqual(self.finding.priority_label, "URGENT")
        self.assertEqual(self.finding.priority_explanation["kev_points"], 25)

    def test_cache_ttl_prevents_unnecessary_upstream_call(self):
        cached = VulnerabilityIntel.objects.create(
            cve_id="CVE-2024-1234",
            kev_listed=False,
            epss_score=Decimal("0.1000"),
            source_retrieved_at=timezone.now(),
            last_refresh_attempt_at=timezone.now(),
            last_refresh_status=VulnerabilityIntel.RefreshStatus.SUCCESS,
        )
        service = IntelligenceService(nvd_client=Mock(), cisa_client=Mock(), epss_client=Mock())

        result = service.refresh_for_finding(self.finding)

        self.assertTrue(result.used_cache)
        self.assertEqual(result.intel.id, cached.id)
        service.nvd_client.fetch.assert_not_called()

    def test_upstream_failure_preserves_stale_cache(self):
        stale = VulnerabilityIntel.objects.create(
            cve_id="CVE-2024-1234",
            kev_listed=True,
            epss_score=Decimal("0.7000"),
            source_retrieved_at=timezone.now() - timedelta(days=2),
            last_refresh_attempt_at=timezone.now() - timedelta(days=2),
            last_refresh_status=VulnerabilityIntel.RefreshStatus.SUCCESS,
        )
        failing = Mock(fetch=Mock(side_effect=RuntimeError("secret stack trace")))
        result = IntelligenceService(nvd_client=failing, cisa_client=failing, epss_client=failing).refresh_for_finding(self.finding)
        stale.refresh_from_db()

        self.assertEqual(result.intel.id, stale.id)
        self.assertEqual(stale.last_refresh_status, VulnerabilityIntel.RefreshStatus.FAILED)
        self.assertEqual(stale.last_safe_error, "Public intelligence providers unavailable.")

    def test_priority_algorithm_boundaries(self):
        self.finding.cvss_score = Decimal("5.0")
        self.finding.affected_asset.criticality = Asset.Criticality.HIGH
        self.finding.affected_asset.internet_exposed = False
        self.finding.affected_asset.save()
        intel = VulnerabilityIntel(cve_id="CVE-2024-9999", kev_listed=False, epss_score=Decimal("0.3000"))

        explanation = PriorityService.score(self.finding, intel)

        self.assertEqual(explanation["cvss_points"], 30)
        self.assertEqual(explanation["epss_points"], 7)
        self.assertEqual(explanation["asset_criticality_points"], 3)
        self.assertEqual(explanation["total"], 40)
        self.assertEqual(explanation["label"], "MEDIUM")

    def test_intelligence_api_permissions(self):
        with patch("apps.intelligence.views.IntelligenceService") as service_class:
            service_class.return_value = self.fake_service()
            self.api.force_authenticate(self.consultant_a)
            ok = self.api.post(reverse("finding-intelligence-refresh", args=[self.finding.id]), {}, format="json")
            self.assertEqual(ok.status_code, status.HTTP_200_OK)
            self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.INTELLIGENCE_REFRESHED, entity_id=self.finding.id).exists())

        self.api.force_authenticate(self.manager_a)
        denied = self.api.post(reverse("finding-intelligence-refresh", args=[self.finding.id]), {}, format="json")
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

        self.api.force_authenticate(self.consultant_b)
        hidden = self.api.get(reverse("finding-intelligence", args=[self.finding.id]))
        self.assertEqual(hidden.status_code, status.HTTP_404_NOT_FOUND)

    def test_no_cve_refresh_returns_validation_failure(self):
        self.finding.cve_id = ""
        self.finding.save()
        self.api.force_authenticate(self.consultant_a)

        response = self.api.post(reverse("finding-intelligence-refresh", args=[self.finding.id]), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
