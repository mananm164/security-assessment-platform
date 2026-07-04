---
title: Logging and monitoring remediation guidance
source_name: OWASP Logging Cheat Sheet
source_url: https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
category: logging_monitoring
---
Logging and monitoring controls should help teams detect exploitation attempts, failed authorization checks, suspicious authentication events, and changes to high-risk records. Logs should include safe identifiers, timestamps, actor IDs, action names, and outcomes, but should not store passwords, tokens, raw request bodies, payment data, or unnecessary personal data. Alerts should be tuned to meaningful events so responders can investigate without being overwhelmed.

Validation should confirm that important events are captured, retained, searchable, and protected from unauthorised changes. Test both successful and denied actions where practical.
