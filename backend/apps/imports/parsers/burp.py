from __future__ import annotations

import re
from html import unescape
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from lxml import etree

from apps.common.exceptions import ImportValidationError

from .base import BaseImporter, NormalisedObservation
from .nmap import sanitise_evidence

_HTML_TAGS = re.compile(r"<[^>]+>")
_PARAMETER_ENTITY_REFERENCE = re.compile(rb"%\s*[A-Za-z_][\w.-]*\s*;")
METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
SEVERITY_LABELS = {
    "high": "HIGH",
    "medium": "MEDIUM",
    "low": "LOW",
    "information": "INFORMATIONAL",
    "informational": "INFORMATIONAL",
    "unknown": "INFORMATIONAL",
    "": "INFORMATIONAL",
}
CONFIDENCE_LABELS = {
    "certain": "Certain",
    "firm": "Firm",
    "tentative": "Tentative",
    "unknown": "Unknown",
    "": "Unknown",
}
IGNORED_TAGS = {"requestresponse", "request", "response", "raw"}


def strip_html(value: str | None, *, max_length: int = 4000) -> str:
    if not value:
        return ""
    return sanitise_evidence(unescape(_HTML_TAGS.sub(" ", value)), max_length=max_length)


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def issue_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")
    return slug[:120] or "burp-issue"


def normalise_severity(value: str | None) -> str:
    return SEVERITY_LABELS.get((value or "").strip().lower(), "INFORMATIONAL")


def normalise_confidence(value: str | None) -> str:
    return CONFIDENCE_LABELS.get((value or "").strip().lower(), "Unknown")


def safe_location(value: str | None) -> str:
    cleaned = strip_html(value, max_length=120)
    return cleaned.strip(" []")


def canonical_origin(value: str | None) -> str | None:
    if not value:
        return None
    candidate = strip_html(value, max_length=500)
    parsed = urlparse(candidate)
    if not parsed.scheme:
        parsed = urlparse(f"https://{candidate}")
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        return None
    if parsed.username or parsed.password:
        return None
    scheme = parsed.scheme.lower()
    hostname = parsed.hostname.lower()
    port = parsed.port
    netloc = hostname
    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        netloc = f"{hostname}:{port}"
    return urlunparse((scheme, netloc, "", "", "", ""))


def canonical_path(value: str | None) -> str:
    if not value:
        return "/"
    cleaned = strip_html(value, max_length=500)
    parsed = urlparse(cleaned)
    path = parsed.path or cleaned.split("?", 1)[0].split("#", 1)[0] or "/"
    if not path.startswith("/"):
        path = f"/{path}"
    return sanitise_evidence(path, max_length=300)


class BurpXmlImporter(BaseImporter):
    source_tool = "BURP"
    max_size_bytes: int

    def __init__(self, *, max_size_bytes: int):
        self.max_size_bytes = max_size_bytes

    def validate(self, content: bytes, filename: str) -> None:
        if Path(filename).suffix.lower() != ".xml":
            raise ImportValidationError("Unsupported file extension for Burp XML import.")
        if not content or not content.strip():
            raise ImportValidationError("Burp XML report is blank.")
        if len(content) > self.max_size_bytes:
            raise ImportValidationError("Burp XML report exceeds the configured size limit.")
        self._validate_preamble(content)
        root = self._parse_root(content)
        if local_name(root.tag) != "issues":
            raise ImportValidationError("Unsupported or malformed Burp XML report.")
        if not any(local_name(child.tag) == "issue" for child in root):
            raise ImportValidationError("Burp XML report does not contain issue records.")

    def parse(self, content: bytes) -> list[NormalisedObservation]:
        self._validate_preamble(content)
        observations: list[NormalisedObservation] = []
        try:
            context = etree.iterparse(
                BytesIO(content),
                events=("end",),
                tag="issue",
                resolve_entities=False,
                no_network=True,
                dtd_validation=False,
                huge_tree=False,
                recover=False,
                remove_comments=True,
            )
            for _, issue in context:
                observation = self._observation_from_issue(issue)
                if observation is not None:
                    observations.append(observation)
                issue.clear()
        except (etree.XMLSyntaxError, ValueError, OSError) as exc:
            raise ImportValidationError("Unsupported or malformed Burp XML report.") from exc
        if not observations:
            raise ImportValidationError("Burp XML report does not contain usable issue records.")
        return observations

    def _parse_root(self, content: bytes):
        parser = etree.XMLParser(
            resolve_entities=False,
            no_network=True,
            load_dtd=False,
            dtd_validation=False,
            huge_tree=False,
            recover=False,
            remove_comments=True,
        )
        try:
            return etree.fromstring(content, parser=parser)
        except (etree.XMLSyntaxError, ValueError) as exc:
            raise ImportValidationError("Unsupported or malformed Burp XML report.") from exc

    def _validate_preamble(self, content: bytes) -> None:
        lowered = content[:4096].lower()
        if b"<!entity" in lowered or _PARAMETER_ENTITY_REFERENCE.search(lowered):
            raise ImportValidationError("Unsupported or malformed Burp XML report.")
        doctype_index = lowered.find(b"<!doctype")
        if doctype_index >= 0:
            end_index = lowered.find(b"]>", doctype_index)
            if end_index < 0:
                end_index = lowered.find(b">", doctype_index)
            doctype = lowered[doctype_index : end_index + 2 if end_index >= 0 else doctype_index + 512]
            if b"system" in doctype or b"public" in doctype or b"<!entity" in doctype:
                raise ImportValidationError("Unsupported or malformed Burp XML report.")

    def _observation_from_issue(self, issue) -> NormalisedObservation | None:
        values = self._safe_issue_values(issue)
        title = values.get("name") or "Burp issue"
        origin = canonical_origin(values.get("host"))
        if not origin:
            return None
        path = canonical_path(values.get("path"))
        location_name = safe_location(values.get("location"))
        method = self._method_from_issue(issue, values.get("path"))
        location = self._raw_location(method=method, path=path, location_name=location_name)
        plugin_id = sanitise_evidence(values.get("type"), max_length=120) or issue_slug(title)
        raw_severity = normalise_severity(values.get("severity"))
        confidence = normalise_confidence(values.get("confidence"))
        description = strip_html(values.get("issuebackground"), max_length=4000)
        remediation = strip_html(values.get("remediationbackground"), max_length=4000)
        evidence = (
            f'Burp reported "{title}" at {origin}{path} '
            f"with {raw_severity.title()} severity and {confidence} confidence."
        )
        if location_name:
            evidence = f"{evidence} Location: {location_name}."

        return NormalisedObservation(
            source_tool=self.source_tool,
            external_id=f"burp:{origin}:{path}:{plugin_id}:{location_name}",
            title=sanitise_evidence(title, max_length=255),
            raw_severity=raw_severity,
            confidence=confidence,
            asset_identifier=origin,
            hostname=urlparse(origin).hostname,
            url=f"{origin}{path}",
            description=description,
            evidence_summary=sanitise_evidence(evidence, max_length=2000),
            suggested_remediation=remediation,
            scanner_plugin_id=plugin_id,
            raw_location=location,
        )

    def _safe_issue_values(self, issue) -> dict[str, str]:
        values: dict[str, str] = {}
        for child in issue:
            name = local_name(child.tag)
            if name in IGNORED_TAGS:
                continue
            if name in {
                "type",
                "name",
                "host",
                "path",
                "location",
                "severity",
                "confidence",
                "issuebackground",
                "remediationbackground",
                "references",
            }:
                values[name] = strip_html("".join(child.itertext()), max_length=4000)
        return values

    def _method_from_issue(self, issue, path_value: str | None) -> str:
        path_element = next((child for child in issue if local_name(child.tag) == "path"), None)
        if path_element is not None:
            method = sanitise_evidence(path_element.get("method"), max_length=12).upper()
            if method in METHODS:
                return method
        if path_value:
            first = path_value.strip().split(" ", 1)[0].upper()
            if first in METHODS:
                return first
        return ""

    def _raw_location(self, *, method: str, path: str, location_name: str) -> str:
        prefix = f"{method} " if method else ""
        suffix = f" [{location_name}]" if location_name else ""
        return sanitise_evidence(f"{prefix}{path}{suffix}", max_length=500)
