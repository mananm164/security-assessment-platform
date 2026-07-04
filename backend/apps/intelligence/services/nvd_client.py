from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings


@dataclass(frozen=True)
class NvdResult:
    description: str
    cvss_score: Decimal | None
    cvss_vector: str
    cwe_ids: list[str]
    references: list[dict]


class NvdClient:
    def __init__(self, *, base_url: str | None = None, api_key: str | None = None, timeout: int = 10):
        self.base_url = base_url or settings.NVD_API_BASE_URL
        self.api_key = api_key if api_key is not None else settings.NVD_API_KEY
        self.timeout = timeout

    def fetch(self, cve_id: str) -> NvdResult:
        url = f"{self.base_url}?{urlencode({'cveId': cve_id})}"
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["apiKey"] = self.api_key
        request = Request(url, headers=headers)
        with urlopen(request, timeout=self.timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return self.parse(payload)

    @staticmethod
    def parse(payload: dict) -> NvdResult:
        vulnerabilities = payload.get("vulnerabilities") or []
        if not vulnerabilities:
            return NvdResult("", None, "", [], [])
        cve = (vulnerabilities[0].get("cve") or {})
        descriptions = cve.get("descriptions") or []
        description = next((item.get("value", "") for item in descriptions if item.get("lang") == "en"), "")
        metrics = cve.get("metrics") or {}
        metric = None
        for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
            values = metrics.get(key) or []
            if values:
                metric = values[0].get("cvssData") or {}
                break
        cvss_score = None
        cvss_vector = ""
        if metric:
            try:
                cvss_score = Decimal(str(metric.get("baseScore")))
            except (InvalidOperation, TypeError):
                cvss_score = None
            cvss_vector = str(metric.get("vectorString") or "")[:255]
        weaknesses = cve.get("weaknesses") or []
        cwe_ids: list[str] = []
        for weakness in weaknesses:
            for desc in weakness.get("description") or []:
                value = desc.get("value")
                if value and value.startswith("CWE-") and value not in cwe_ids:
                    cwe_ids.append(value)
        references = []
        for ref in cve.get("references", {}).get("referenceData", [])[:10]:
            url = str(ref.get("url") or "")[:500]
            if url.startswith(("https://", "http://")):
                references.append({"url": url, "title": str(ref.get("source") or url)[:160]})
        return NvdResult(description[:4000], cvss_score, cvss_vector, cwe_ids, references)
