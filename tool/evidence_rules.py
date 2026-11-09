"""
Evidence rules catalogue for the evidence-analysis pipeline.

Each entry defines, for a key control, what evidence SHOULD exist and how to
recognise it. This is the deterministic (non-AI) layer: it is transparent,
repeatable, and auditable — exactly what a control owner needs to trust a
completeness check.

Fields per rule:
  csf        : the NIST CSF 2.0 subcategory this evidence supports
  iso        : the matching ISO/IEC 27001:2022 Annex A control(s) / clause(s)
  title      : what the evidence demonstrates
  required   : True if absence is a finding (not just a nice-to-have)
  freshness_days : evidence older than this is flagged STALE
  keywords   : content terms (any match links a document to this control)
  filename_hints : filename fragments that also link a document

Keep this catalogue curated and explainable — a reviewer must be able to see
*why* a document was matched to a control.
"""

EVIDENCE_RULES = [
    # ---- Govern ----
    dict(csf="GV.PO-01", iso=["A.5.1"], title="Information security policy exists & is approved",
         required=True, freshness_days=365,
         keywords=["information security policy", "security policy", "policy statements"],
         filename_hints=["information_security_policy", "infosec_policy", "security_policy"]),
    dict(csf="GV.RR-02", iso=["A.5.2"], title="Security roles & responsibilities are defined",
         required=True, freshness_days=365,
         keywords=["roles and responsibilities", "accountable for information security",
                   "responsibilities"],
         filename_hints=["roles", "responsibilit"]),
    dict(csf="GV.RM-06", iso=["Cl.6"], title="Documented risk assessment method / risk register",
         required=True, freshness_days=365,
         keywords=["risk register", "likelihood", "risk score", "risk methodology"],
         filename_hints=["risk_register", "risk_assessment", "risk-register"]),
    dict(csf="GV.SC-06", iso=["A.5.19", "A.5.20"], title="Supplier / third-party security assessment",
         required=True, freshness_days=365,
         keywords=["supplier security", "vendor assessment", "third-party security",
                   "due diligence"],
         filename_hints=["supplier", "vendor", "third_party", "tpra"]),
    # ---- Identify ----
    dict(csf="ID.AM-01", iso=["A.5.9", "A.8.1"], title="Asset inventory is maintained",
         required=True, freshness_days=180,
         keywords=["asset inventory", "asset_id", "inventory of"],
         filename_hints=["asset_inventory", "asset-inventory", "assets"]),
    dict(csf="ID.RA-05", iso=["Cl.6"], title="Risk assessment combining threats/vulns/impact",
         required=True, freshness_days=365,
         keywords=["risk assessment", "threat", "impact analysis"],
         filename_hints=["risk_assessment", "risk-assessment"]),
    # ---- Protect ----
    dict(csf="PR.AA-05", iso=["A.5.18", "A.8.2"], title="Access reviewed on least-privilege basis",
         required=True, freshness_days=120,
         keywords=["least privilege", "access review", "access rights", "access level"],
         filename_hints=["access_review", "access_control", "access-review"]),
    dict(csf="PR.AT-01", iso=["A.6.3"], title="Staff security awareness training delivered",
         required=True, freshness_days=365,
         keywords=["awareness training", "security training", "phishing"],
         filename_hints=["training", "awareness"]),
    dict(csf="PR.DS-01", iso=["A.8.24"], title="Data-at-rest protection / encryption",
         required=True, freshness_days=365,
         keywords=["encryption", "encrypted", "at rest"],
         filename_hints=["encryption", "crypto"]),
    dict(csf="PR.DS-11", iso=["A.8.13"], title="Backups performed AND restore-tested",
         required=True, freshness_days=180,
         keywords=["backup", "restore test", "recovery test"],
         filename_hints=["backup", "restore"]),
    dict(csf="PR.PS-02", iso=["A.8.8"], title="Patch / vulnerability management records",
         required=True, freshness_days=120,
         keywords=["patch", "patching", "vulnerability management", "updates applied"],
         filename_hints=["patch", "vulnerability", "patching"]),
    # ---- Detect ----
    dict(csf="DE.CM-01", iso=["A.8.16", "A.8.15"], title="Monitoring / logging of systems",
         required=True, freshness_days=90,
         keywords=["log review", "log monitoring", "logging", "monitoring", "alert", "siem"],
         filename_hints=["monitoring", "siem", "log_review", "audit_log", "logging"]),
    # ---- Respond ----
    dict(csf="RS.MA-01", iso=["A.5.24", "A.5.26"], title="Incident response plan exists",
         required=True, freshness_days=365,
         keywords=["incident response plan", "incident response procedure", "containment"],
         filename_hints=["incident_response", "incident-response", "ir_plan"]),
    # ---- Recover ----
    dict(csf="RC.RP-01", iso=["A.5.29", "A.5.30"], title="Recovery / business-continuity plan",
         required=True, freshness_days=365,
         keywords=["recovery plan", "business continuity", "disaster recovery", "continuity plan"],
         filename_hints=["recovery_plan", "continuity", "bcp", "dr_plan"]),
]


def rule_index():
    return {r["csf"]: r for r in EVIDENCE_RULES}


if __name__ == "__main__":
    print(f"{len(EVIDENCE_RULES)} evidence rules across functions:")
    from collections import Counter
    c = Counter(r["csf"].split(".")[0] for r in EVIDENCE_RULES)
    print(dict(c))
    req = sum(1 for r in EVIDENCE_RULES if r["required"])
    print(f"required: {req}/{len(EVIDENCE_RULES)}")
