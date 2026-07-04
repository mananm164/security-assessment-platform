from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
from urllib.request import Request, urlopen

from django.conf import settings


@dataclass(frozen=True)
class CisaKevResult:
    listed: bool
    date_added: date | None


class CisaKevClient:
    def __init__(self, *, url: str | None = None, timeout: int = 10):
        self.url = url or settings.CISA_KEV_URL
        self.timeout = timeout

    def fetch(self, cve_id: str) -> CisaKevResult:
        request = Request(self.url, headers={"Accept": "application/json"})
        with urlopen(request, timeout=self.timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return self.parse(payload, cve_id)

    @staticmethod
    def parse(payload: dict, cve_id: str) -> CisaKevResult:
        wanted = cve_id.upper()
        for item in payload.get("vulnerabilities") or []:
            if str(item.get("cveID") or "").upper() == wanted:
                parsed_date = None
                raw_date = item.get("dateAdded")
                if raw_date:
                    try:
                        parsed_date = date.fromisoformat(raw_date)
                    except ValueError:
                        parsed_date = None
                return CisaKevResult(True, parsed_date)
        return CisaKevResult(False, None)
