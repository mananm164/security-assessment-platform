from __future__ import annotations

import json
import re
from html import unescape
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from apps.common.exceptions import ImportValidationError

from .base import BaseImporter, NormalisedObservation
from .nmap import sanitise_evidence

_HTML_TAGS = re.compile(r"<[^>]+>")
RAW_MESSAGE_KEYS = {
    "requestheader",
    "requestbody",
    "responseheader",
    "responsebody",
    "requestheaders",
    "responseheaders",
    "requestbodybase64",
    "responsebodybase64",
}
RISK_LABELS = {
    "0": "INFORMATIONAL",
    "1": "LOW",
    "2": "MEDIUM",
    "3": "HIGH",
}


def strip_html(value: str | None) -> str:
    if not value:
        return ""
    return sanitise_evidence(unescape(_HTML_TAGS.sub(" ", value)))


def canonical_url(value: str) -> str:
    parsed = urlparse(value)
    if not parsed.scheme or not parsed.netloc:
        raise ImportValidationError("Unsupported or malformed ZAP JSON report.")
    path = parsed.path or "/"
    return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), path, "", "", ""))


def site_base_url(site: dict) -> str:
    name = site.get("@name") or site.get("name")
    if name:
        try:
            parsed = urlparse(name)
            if parsed.scheme and parsed.netloc:
                return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), "", "", "", ""))
        except ValueError:
            pass

    host = site.get("@host") or site.get("host")
    port = site.get("@port") or site.get("port")
    ssl = str(site.get("@ssl") or site.get("ssl") or "false").lower() == "true"
    if not host:
        raise ImportValidationError("Unsupported or malformed ZAP JSON report.")
    scheme = "https" if ssl else "http"
    netloc = host.lower()
    if port and str(port) not in {"80", "443"}:
        netloc = f"{netloc}:{port}"
    return f"{scheme}://{netloc}"


class ZapJsonImporter(BaseImporter):
    source_tool = "ZAP"
    max_size_bytes: int

    def __init__(self, *, max_size_bytes: int):
        self.max_size_bytes = max_size_bytes

    def validate(self, content: bytes, filename: str) -> None:
        if Path(filename).suffix.lower() != ".json":
            raise ImportValidationError("Unsupported file extension for ZAP JSON import.")
        if not content or not content.strip():
            raise ImportValidationError("ZAP JSON report is blank.")
        if len(content) > self.max_size_bytes:
            raise ImportValidationError("ZAP JSON report exceeds the configured size limit.")
        data = self._load_json(content)
        self._validate_shape(data)
        if self._contains_raw_messages(data):
            raise ImportValidationError("ZAP reports with raw HTTP messages are unsupported.")

    def parse(self, content: bytes) -> list[NormalisedObservation]:
        data = self._load_json(content)
        self._validate_shape(data)
        if self._contains_raw_messages(data):
            raise ImportValidationError("ZAP reports with raw HTTP messages are unsupported.")

        observations: list[NormalisedObservation] = []
        for site in data["site"]:
            base_url = site_base_url(site)
            host = urlparse(base_url).hostname
            alerts = site.get("alerts") or []
            if not isinstance(alerts, list):
                raise ImportValidationError("Unsupported or malformed ZAP JSON report.")
            for alert in alerts:
                if not isinstance(alert, dict):
                    continue
                plugin_id = str(alert.get("pluginid") or alert.get("alertRef") or "unknown")
                title = str(alert.get("alert") or alert.get("name") or f"ZAP alert {plugin_id}")
                raw_severity = self._risk_label(alert)
                confidence = str(alert.get("confidence") or "")
                description = strip_html(alert.get("desc"))
                remediation = strip_html(alert.get("solution"))
                references = [strip_html(alert.get("reference"))] if strip_html(alert.get("reference")) else []
                cwe_ids = self._ids_from_value(alert.get("cweid"))
                instances = alert.get("instances") or []
                if not isinstance(instances, list):
                    raise ImportValidationError("Unsupported or malformed ZAP JSON report.")
                for instance in instances:
                    if not isinstance(instance, dict):
                        continue
                    uri = instance.get("uri")
                    if not uri:
                        continue
                    location = canonical_url(str(uri))
                    parameter = sanitise_evidence(str(instance.get("param") or ""), max_length=120)
                    method = sanitise_evidence(str(instance.get("method") or ""), max_length=20)
                    node_name = sanitise_evidence(str(instance.get("nodeName") or ""), max_length=120)
                    param_component = f":param:{parameter}" if parameter else ":param:"
                    evidence_parts = []
                    if method:
                        evidence_parts.append(f"method={method}")
                    if parameter:
                        evidence_parts.append(f"param={parameter}")
                    if node_name:
                        evidence_parts.append(f"node={node_name}")

                    observations.append(
                        NormalisedObservation(
                            source_tool=self.source_tool,
                            external_id=f"zap:{plugin_id}:{location}{param_component}",
                            title=title,
                            raw_severity=raw_severity,
                            confidence=confidence,
                            asset_identifier=base_url,
                            hostname=host,
                            url=location,
                            description=description,
                            evidence_summary=sanitise_evidence("; ".join(evidence_parts)),
                            suggested_remediation=remediation,
                            cwe_ids=cwe_ids,
                            scanner_plugin_id=plugin_id,
                            references=references,
                            raw_location=f"{location}{param_component}",
                        )
                    )
        return observations

    def _load_json(self, content: bytes) -> dict:
        try:
            decoded = content.decode("utf-8")
            data = json.loads(decoded)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ImportValidationError("Unsupported or malformed ZAP JSON report.") from exc
        if not isinstance(data, dict):
            raise ImportValidationError("Unsupported or malformed ZAP JSON report.")
        return data

    def _validate_shape(self, data: dict) -> None:
        if "site" not in data or not isinstance(data["site"], list):
            raise ImportValidationError("Unsupported or malformed ZAP JSON report.")

    def _contains_raw_messages(self, value) -> bool:
        if isinstance(value, dict):
            for key, child in value.items():
                if str(key).lower() in RAW_MESSAGE_KEYS:
                    return True
                if self._contains_raw_messages(child):
                    return True
        if isinstance(value, list):
            return any(self._contains_raw_messages(item) for item in value)
        return False

    def _risk_label(self, alert: dict) -> str:
        risk_code = str(alert.get("riskcode") or "").strip()
        if risk_code in RISK_LABELS:
            return RISK_LABELS[risk_code]
        riskdesc = str(alert.get("riskdesc") or "").lower()
        for label in ["informational", "low", "medium", "high"]:
            if label in riskdesc:
                return label.upper()
        return ""

    def _ids_from_value(self, value) -> list[str]:
        if value in [None, "", "-1"]:
            return []
        return [str(value)]
