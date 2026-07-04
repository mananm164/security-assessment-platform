from apps.findings.selectors import visible_findings_for


def visible_finding_for_intelligence(user, finding_id):
    return visible_findings_for(user).filter(id=finding_id).first()
