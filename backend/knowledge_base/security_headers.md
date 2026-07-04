---
title: Security headers remediation guidance
source_name: OWASP Secure Headers Project
source_url: https://owasp.org/www-project-secure-headers/
category: security_headers
---
Security headers reduce browser-side attack surface when they are deployed consistently through the application edge. Prioritise HTTPS-only delivery, HSTS after confirming TLS coverage, a content security policy that reflects actual script and asset needs, and defensive defaults such as frame restrictions, referrer limits, and MIME sniffing protection. Header changes should be tested in a staging environment because overly broad or overly strict policies can break authentication, file downloads, or embedded business workflows.

Validation should confirm headers on authenticated and unauthenticated routes, redirects, error pages, and static assets. Record exceptions with an owner and review date.
