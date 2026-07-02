from __future__ import annotations

import re
from pathlib import Path

from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException

from apps.common.exceptions import ImportValidationError

from .base import BaseImporter, NormalisedObservation

MAX_EVIDENCE_LENGTH = 2000
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_WHITESPACE = re.compile(r"\s+")


def sanitise_evidence(value: str | None, *, max_length: int = MAX_EVIDENCE_LENGTH) -> str:
    if not value:
        return ""
    cleaned = _CONTROL_CHARS.sub("", value)
    cleaned = _WHITESPACE.sub(" ", cleaned).strip()
    if len(cleaned) <= max_length:
        return cleaned
    marker = " ... [truncated]"
    return cleaned[: max_length - len(marker)].rstrip() + marker


class NmapXmlImporter(BaseImporter):
    source_tool = "NMAP"
    max_size_bytes: int

    def __init__(self, *, max_size_bytes: int):
        self.max_size_bytes = max_size_bytes

    def validate(self, content: bytes, filename: str) -> None:
        if Path(filename).suffix.lower() != ".xml":
            raise ImportValidationError("Unsupported file extension for Nmap XML import.")
        if not content or not content.strip():
            raise ImportValidationError("Nmap XML report is blank.")
        if len(content) > self.max_size_bytes:
            raise ImportValidationError("Nmap XML report exceeds the configured size limit.")
        lowered = content[:2048].lower()
        if b"<!doctype" in lowered or b"<!entity" in lowered:
            raise ImportValidationError("Unsupported or malformed Nmap XML report.")
        self._parse_root(content)

    def parse(self, content: bytes) -> list[NormalisedObservation]:
        root = self._parse_root(content)
        if root.tag != "nmaprun":
            raise ImportValidationError("Unsupported or malformed Nmap XML report.")

        observations: list[NormalisedObservation] = []
        for host in root.findall("host"):
            host_identifier, hostname = self._host_identity(host)
            if not host_identifier and not hostname:
                continue
            asset_identifier = host_identifier or hostname
            for port_element in host.findall("ports/port"):
                state = port_element.find("state")
                if state is None or state.get("state") != "open":
                    continue

                protocol = (port_element.get("protocol") or "").lower()
                port_text = port_element.get("portid")
                if not protocol or not port_text or not port_text.isdigit():
                    continue
                port = int(port_text)
                service = port_element.find("service")
                service_name = service.get("name") if service is not None else None
                evidence = self._service_evidence(state, service)
                location = f"{asset_identifier}:{port}/{protocol}"
                service_suffix = f" ({service_name})" if service_name else ""

                observations.append(
                    NormalisedObservation(
                        source_tool=self.source_tool,
                        external_id=f"host:{asset_identifier}:{protocol}:{port}:port",
                        title=f"Open {protocol.upper()}/{port}{service_suffix}",
                        asset_identifier=asset_identifier,
                        hostname=hostname,
                        port=port,
                        protocol=protocol,
                        description=(
                            f"Nmap observed an open {protocol.upper()} port {port}"
                            f" with the {service_name or 'unknown'} service."
                        ),
                        evidence_summary=evidence,
                        scanner_plugin_id="nmap-port",
                        raw_location=location,
                    )
                )

                for script in port_element.findall("script"):
                    script_id = script.get("id")
                    if not script_id:
                        continue
                    script_output = sanitise_evidence(script.get("output"))
                    observations.append(
                        NormalisedObservation(
                            source_tool=self.source_tool,
                            external_id=f"host:{asset_identifier}:{protocol}:{port}:script:{script_id}",
                            title=f"Nmap NSE: {script_id}",
                            asset_identifier=asset_identifier,
                            hostname=hostname,
                            port=port,
                            protocol=protocol,
                            description=(
                                f"Nmap NSE script {script_id} returned output for "
                                f"{protocol.upper()}/{port}."
                            ),
                            evidence_summary=script_output,
                            scanner_plugin_id=script_id,
                            raw_location=location,
                        )
                    )
        return observations

    def _parse_root(self, content: bytes):
        try:
            return ElementTree.fromstring(content)
        except (DefusedXmlException, ElementTree.ParseError, ValueError) as exc:
            raise ImportValidationError("Unsupported or malformed Nmap XML report.") from exc

    def _host_identity(self, host) -> tuple[str | None, str | None]:
        hostname = None
        hostname_element = host.find("hostnames/hostname")
        if hostname_element is not None:
            hostname = hostname_element.get("name") or None

        addresses = host.findall("address")
        for address in addresses:
            address_type = address.get("addrtype")
            if address_type in {"ipv4", "ipv6"} and address.get("addr"):
                return address.get("addr"), hostname
        if hostname:
            return hostname, hostname
        return None, None

    def _service_evidence(self, state, service) -> str:
        parts = [f"state={state.get('state', 'unknown')}"]
        if service is not None:
            for key in ["name", "product", "version", "extrainfo"]:
                value = service.get(key)
                if value:
                    parts.append(f"{key}={value}")
        return sanitise_evidence("; ".join(parts))
