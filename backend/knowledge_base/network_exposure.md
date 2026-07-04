---
title: Network exposure remediation guidance
source_name: CIS Controls
source_url: https://www.cisecurity.org/controls
category: network_exposure
---
Network exposure findings should be remediated by reducing reachability to the minimum audience required for the business service. Confirm whether the asset is internet-facing, which ports and protocols are exposed, and whether administrative or database interfaces are reachable from untrusted networks. Preferred fixes include removing public listeners, applying firewall allow lists, placing services behind authenticated gateways, and enforcing modern TLS for externally reachable applications.

Validation should confirm that unnecessary ports are closed from the relevant network perspective and that monitoring alerts on future exposure changes. Document accepted exposure with an owner and review date.
