from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings


@dataclass(frozen=True)
class EpssResult:
    score: Decimal | None
    percentile: Decimal | None


class EpssClient:
    def __init__(self, *, base_url: str | None = None, timeout: int = 10):
        self.base_url = base_url or settings.EPSS_API_BASE_URL
        self.timeout = timeout

    def fetch(self, cve_id: str) -> EpssResult:
        url = f"{self.base_url}?{urlencode({'cve': cve_id})}"
        request = Request(url, headers={"Accept": "application/json"})
        with urlopen(request, timeout=self.timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return self.parse(payload)

    @staticmethod
    def parse(payload: dict) -> EpssResult:
        rows = payload.get("data") or []
        if not rows:
            return EpssResult(None, None)
        row = rows[0]
        def decimal_or_none(value):
            try:
                return Decimal(str(value))
            except (InvalidOperation, TypeError):
                return None
        return EpssResult(decimal_or_none(row.get("epss")), decimal_or_none(row.get("percentile")))
