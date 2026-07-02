from __future__ import annotations

import ipaddress
import re
from html import unescape
from pathlib import Path

from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException

from apps.common.exceptions import ImportValidationError

from .base import BaseImporter, NormalisedObservation
from .nmap import sanitise_evidence

_HTML_TAGS = re.compile(r"<[^>]+>")
_CVE_PATTERN = re.compile(r"CVE[-_\s]?(\d{4})[-_\s]?(\d{4,7})", re.IGNORECASE)
_CWE_PATTERN = re.compile(r"(?:CWE[-_\s]*)?(\d{1,6})", re.IGNORECASE)
SEVERITY_LABELS = {
    "0": "INFORMATIONAL",
    "1": "LOW",
    "2": "MEDIUM",
    "3": "HIGH",
    "4": "CRITICAL",
}


def strip_html(value: str | None, *, max_length: int = 4000) -> str:
    if not value:
        return ""
    return sanitise_evidence(unescape(_HTML_TAGS.sub(" ", value)), max_length=max_length)


def normalise_ip(value: str | None) -> str | None:
    if not value:
        return None
    candidate = sanitise_evidence(value, max_length=80)
    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        return None


def safe_hostname(value: str | None) -> str | None:
    if not value:
        return None
    hostname = sanitise_evidence(value, max_length=255).strip().lower().rstrip(".")
    return hostname or None


def normalise_ids(pattern: re.Pattern[str], values: list[str]) -> list[str]:
    seen: set[str] = set()
    normalised: list[str] = []
    for value in values:
        for match in pattern.finditer(value or ""):
            if pattern is _CVE_PATTERN:
                item = f"CVE-{match.group(1)}-{match.group(2)}".upper()
            else:
                number = match.group(1).lstrip("0") or "0"
                if number == "0":
                    continue
                item = f"CWE-{number}"
            if item not in seen:
                seen.add(item)
                normalised.append(item)
    return normalised


def normalise_cvss(value: str | None) -> str | None:
    if not value:
        return None
    candidate = sanitise_evidence(value, max_length=20)
    try:
        score = float(candidate)
    except ValueError:
        return None
    if score < 0 or score > 10:
        return None
    return f"{score:.1f}"


class NessusXmlImporter(BaseImporter):
    source_tool = "NESSUS"
    max_size_bytes: int

    def __init__(self, *, max_size_bytes: int):
        self.max_size_bytes = max_size_bytes

    def validate(self, content: bytes, filename: str) -> None:
        if Path(filename).suffix.lower() != ".nessus":
            raise ImportValidationError("Unsupported file extension for Nessus import.")
        if not content or not content.strip():
            raise ImportValidationError("Nessus report is blank.")
        if len(content) > self.max_size_bytes:
            raise ImportValidationError("Nessus report exceeds the configured size limit.")
        lowered = content[:4096].lower()
        if b"<!doctype" in lowered or b"<!entity" in lowered:
            raise ImportValidationError("Unsupported or malformed Nessus report.")
        root = self._parse_root(content)
        self._extract_observations(root)

    def parse(self, content: bytes) -> list[NormalisedObservation]:
        root = self._parse_root(content)
        return self._extract_observations(root)

    def _parse_root(self, content: bytes):
        try:
            return ElementTree.fromstring(content)
        except (DefusedXmlException, ElementTree.ParseError, ValueError) as exc:
            raise ImportValidationError("Unsupported or malformed Nessus report.") from exc

    def _extract_observations(self, root) -> list[NormalisedObservation]:
        if self._tag_name(root.tag) != "NessusClientData_v2":
            raise ImportValidationError("Unsupported or malformed Nessus report.")
        report = self._first_child(root, "Report")
        if report is None:
            raise ImportValidationError("Nessus report does not contain a Report element.")

        observations: list[NormalisedObservation] = []
        hosts = self._children(report, "ReportHost")
        if not hosts:
            raise ImportValidationError("Nessus report does not contain usable hosts.")

        has_report_item = False
        for host in hosts:
            host_ip, hostname = self._host_identity(host)
            host_identity = host_ip or hostname
            if not host_identity:
                continue
            items = self._children(host, "ReportItem")
            if items:
                has_report_item = True
            for item in items:
                plugin_id = sanitise_evidence(item.get("pluginID"), max_length=80)
                if not plugin_id:
                    continue
                title = sanitise_evidence(item.get("pluginName"), max_length=255) or f"Nessus plugin {plugin_id}"
                protocol = sanitise_evidence(item.get("protocol"), max_length=20).lower()
                service_name = sanitise_evidence(item.get("svc_name"), max_length=80)
                port = self._port_from_value(item.get("port"))
                raw_severity = SEVERITY_LABELS.get(str(item.get("severity") or "").strip(), "")
                location = self._location(host_identity, port, protocol, service_name)
                candidate_cvss = self._candidate_cvss(item)
                candidate_vector = self._candidate_vector(item)
                description = self._description(item)
                remediation = strip_html(self._child_text(item, "solution"), max_length=4000)
                cve_ids = normalise_ids(_CVE_PATTERN, self._child_texts(item, "cve"))
                cwe_ids = normalise_ids(_CWE_PATTERN, self._child_texts(item, "cwe"))
                references = [
                    value
                    for value in (strip_html(text, max_length=500) for text in self._child_texts(item, "see_also"))
                    if value
                ]
                evidence = f'Nessus plugin {plugin_id} reported "{title}" on {location}.'
                if candidate_cvss:
                    evidence = f"{evidence} Candidate CVSS score: {candidate_cvss}."
                if candidate_vector:
                    evidence = f"{evidence} Candidate CVSS vector supplied."

                observations.append(
                    NormalisedObservation(
                        source_tool=self.source_tool,
                        external_id=f"nessus:{host_identity}:{protocol or 'unknown'}:{port if port is not None else 'unknown'}:{plugin_id}",
                        title=title,
                        raw_severity=raw_severity,
                        asset_identifier=host_identity,
                        hostname=hostname,
                        port=port,
                        protocol=protocol,
                        description=description,
                        evidence_summary=sanitise_evidence(evidence, max_length=2000),
                        suggested_remediation=remediation,
                        cve_ids=cve_ids,
                        cwe_ids=cwe_ids,
                        scanner_plugin_id=plugin_id,
                        references=references,
                        raw_location=location,
                        candidate_cvss_score=candidate_cvss,
                        candidate_cvss_vector=candidate_vector,
                    )
                )

        if not has_report_item:
            raise ImportValidationError("Nessus report does not contain ReportItem elements.")
        if not observations:
            raise ImportValidationError("Nessus report does not contain usable ReportItems.")
        return observations

    def _host_identity(self, host) -> tuple[str | None, str | None]:
        tags = self._host_property_tags(host)
        host_ip = normalise_ip(tags.get("host-ip"))
        hostname = safe_hostname(tags.get("host-fqdn") or host.get("name"))
        return host_ip, hostname

    def _host_property_tags(self, host) -> dict[str, str]:
        tags: dict[str, str] = {}
        host_properties = self._first_child(host, "HostProperties")
        if host_properties is None:
            return tags
        for tag in self._children(host_properties, "tag"):
            name = sanitise_evidence(tag.get("name"), max_length=80).lower()
            if name:
                tags[name] = strip_html(tag.text, max_length=255)
        return tags

    def _description(self, item) -> str:
        parts = []
        synopsis = strip_html(self._child_text(item, "synopsis"), max_length=1000)
        description = strip_html(self._child_text(item, "description"), max_length=3000)
        if synopsis:
            parts.append(f"Synopsis: {synopsis}")
        if description:
            parts.append(f"Description: {description}")
        return sanitise_evidence(" ".join(parts), max_length=4000)

    def _candidate_cvss(self, item) -> str | None:
        return normalise_cvss(self._child_text(item, "cvss3_base_score") or self._child_text(item, "cvss_base_score"))

    def _candidate_vector(self, item) -> str | None:
        return sanitise_evidence(
            self._child_text(item, "cvss3_vector") or self._child_text(item, "cvss_vector"),
            max_length=120,
        ) or None

    def _location(self, host_identity: str, port: int | None, protocol: str, service_name: str) -> str:
        port_text = str(port) if port is not None else "unknown"
        protocol_text = protocol or "unknown"
        service_suffix = f" ({service_name})" if service_name else ""
        return f"{host_identity}:{port_text}/{protocol_text}{service_suffix}"

    def _port_from_value(self, value: str | None) -> int | None:
        if value is None or not str(value).isdigit():
            return None
        port = int(value)
        if port < 0 or port > 65535:
            return None
        return port

    def _child_text(self, element, tag_name: str) -> str:
        child = self._first_child(element, tag_name)
        return child.text or "" if child is not None else ""

    def _child_texts(self, element, tag_name: str) -> list[str]:
        return [child.text or "" for child in self._children(element, tag_name)]

    def _first_child(self, element, tag_name: str):
        return next(iter(self._children(element, tag_name)), None)

    def _children(self, element, tag_name: str) -> list:
        return [child for child in list(element) if self._tag_name(child.tag) == tag_name]

    def _tag_name(self, value: str) -> str:
        return value.rsplit("}", 1)[-1]
