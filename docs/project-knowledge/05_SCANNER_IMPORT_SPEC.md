# Scanner Import Specification

## Product boundary
SARP receives exported reports from authorised security tools. It does not initiate scans, accept arbitrary target URLs/IP addresses, run scanner commands, schedule scans or store credentials for scanner tools.

## Supported import formats

| Tool | Input format | Initial purpose |
|---|---|---|
| Nmap | XML (`-oX`) | Hosts, ports, services, selected NSE observations |
| OWASP ZAP | Traditional JSON | Web/API alerts, risk, URL, CWE, solution |
| Nessus | Native `.nessus` XML | Infrastructure plugin findings, CVE, CVSS, remediation |
| Burp Suite | XML issue export | Manually validated web/API issues, severity, confidence, location |

## Shared lifecycle

```text
1. Consultant selects an authorised Assessment.
2. Uploads a supported exported file or runs a local management command.
3. SARP validates metadata and report structure.
4. Tool parser creates normalised ScannerObservation records.
5. SARP computes fingerprints and detects candidates for duplicate review.
6. Consultant reviews an import preview.
7. Consultant marks observations as confirmed, false positive, duplicate, accepted risk, or promotes them to a Finding.
8. SARP records audit events and updates dashboards.
```

## Data contract: NormalisedObservation

```python
@dataclass
class NormalisedObservation:
    source_tool: str
    external_id: str
    title: str
    raw_severity: str | None
    confidence: str | None
    asset_identifier: str | None
    port: int | None
    protocol: str | None
    url: str | None
    description: str
    evidence_summary: str
    suggested_remediation: str | None
    cve_ids: list[str]
    cwe_ids: list[str]
    scanner_plugin_id: str | None
    references: list[str]
    raw_location: str | None
```

Parsers must return normalised data. They must not create database records directly. A service layer is responsible for matching/creating assets, writing observations, deduplication and audit events.

## Base importer contract

```python
class BaseImporter(ABC):
    source_tool: str

    @abstractmethod
    def validate(self, content: bytes, filename: str) -> None:
        """Raise a safe domain validation error when unsupported or malformed."""

    @abstractmethod
    def parse(self, content: bytes) -> list[NormalisedObservation]:
        """Return normalised observations; never persist records here."""
```

## Tool-specific mapping

### Nmap XML
- Host address/hostname → Asset candidate.
- Port + protocol + service → exposure observation.
- NSE script ID/output → observation title/evidence.
- Default state: `NEW`; never automatically create a Finding from an open port alone.

**Nmap fingerprint:** assessment + asset + protocol + port + NSE script ID.

### ZAP JSON
- Alert name → title.
- Risk level → raw severity.
- URL/parameter → asset and location.
- Alert ID → scanner plugin ID.
- CWE ID → `cwe_ids`.
- Solution → suggested remediation.

**ZAP fingerprint:** assessment + canonical URL + alert ID + parameter/location.

### Nessus `.nessus`
- ReportHost → asset candidate.
- ReportItem plugin ID → scanner plugin ID.
- CVE, CVSS, plugin output, solution → normalised fields.
- Port/protocol/service → affected location.

**Nessus fingerprint:** assessment + asset + port + protocol + plugin ID.

### Burp XML
- Issue name → title.
- Severity + confidence → raw severity/confidence.
- Canonical URL/path/parameter → location.
- Issue detail → redacted description/evidence summary.
- Remediation background → suggested remediation.

**Burp fingerprint:** assessment + canonical URL + issue type + parameter/location.

## Triage statuses

```text
NEW             Imported but not yet reviewed.
CONFIRMED       Consultant has verified it is a security concern.
FALSE_POSITIVE  Scanner result is not a real issue in context.
DUPLICATE       Better represented by another observation/finding.
ACCEPTED_RISK   Risk is intentionally accepted with documented reason/approver.
PROMOTED        Linked to a confirmed Finding.
```

## Deduplication rules
- Same tool/source fingerprint within the same Assessment: update `last_seen_at`; do not create another observation.
- Different tool sources can be *suggested* as duplicates, but never auto-merged.
- Missing from a later import means `Not observed in latest import`; it is not proof of remediation and must not close a Finding.

## Management command first

```bash
python manage.py import_scan \
  --assessment-id 1 \
  --tool nmap \
  --file fixtures/nmap/sample.xml
```

The React upload wizard comes only after this command and parser tests are reliable.

## Import API target

```text
POST /api/v1/assessments/{assessment_id}/imports/
GET  /api/v1/imports/{id}/
GET  /api/v1/imports/{id}/observations/
POST /api/v1/observations/{id}/triage/
POST /api/v1/observations/{id}/promote/
```

## Required parser tests
- Valid fixture parses expected data.
- Invalid structure gives a safe validation response.
- XML parser has no external-entity resolution.
- Parser does not persist raw secret-bearing evidence.
- Import requires assigned Client scope.
- Reimport updates `last_seen_at` rather than duplicating.
