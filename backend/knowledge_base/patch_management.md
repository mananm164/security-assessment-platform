---
title: Patch-management remediation guidance
source_name: CISA Known Exploited Vulnerabilities Catalog
source_url: https://www.cisa.gov/known-exploited-vulnerabilities-catalog
category: patch_management
---
Patch remediation should start with asset ownership, affected version confirmation, and business criticality. For known exploited vulnerabilities, prioritise supported vendor fixes or documented mitigations and track any temporary compensating control to expiry. Production updates should include rollback planning, maintenance-window approval, and post-change verification that the vulnerable version or component is no longer reachable.

Validation should use a safe version check, authenticated configuration review, or targeted scanner retest. Avoid treating a missing scanner alert alone as proof of remediation when inventory or credentials are incomplete.
