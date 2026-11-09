"""
ISO/IEC 27001:2022 reference data + a curated NIST CSF 2.0 -> ISO 27001:2022 crosswalk.

WHAT THIS IS
------------
- ISO_CONTROLS      : all 93 ISO/IEC 27001:2022 Annex A controls (exact titles), by theme.
- MANAGEMENT_CLAUSES: ISO/IEC 27001:2022 clauses 4-10 (the ISMS itself), referenced where a
                      CSF outcome is about *management* rather than a specific Annex A control.
- CATEGORY_MAPPING  : the base mapping from each CSF 2.0 category to the ISO refs it aligns with.
- SUBCATEGORY_OVERRIDES: finer, subcategory-specific refs where the category default is too broad.

HONESTY / SOURCING (say this in interviews)
-------------------------------------------
The Annex A control list is authoritative (ISO/IEC 27001:2022). The CSF->ISO *mapping* here is a
**curated, analyst-built crosswalk** -- it is informed by how the frameworks line up, NOT a verbatim
copy of NIST's official Informative References. Framework mappings are inherently many-to-many and
involve judgement. For production use, validate against NIST's official CSF 2.0 Informative
References and ISO/IEC 27002:2022. This file is transparent about that on purpose.
"""

# ---- ISO/IEC 27001:2022 Annex A controls (93), exact 2022 titles -------------------
ISO_CONTROLS = {
    # A.5 Organizational (37)
    "A.5.1": "Policies for information security",
    "A.5.2": "Information security roles and responsibilities",
    "A.5.3": "Segregation of duties",
    "A.5.4": "Management responsibilities",
    "A.5.5": "Contact with authorities",
    "A.5.6": "Contact with special interest groups",
    "A.5.7": "Threat intelligence",
    "A.5.8": "Information security in project management",
    "A.5.9": "Inventory of information and other associated assets",
    "A.5.10": "Acceptable use of information and other associated assets",
    "A.5.11": "Return of assets",
    "A.5.12": "Classification of information",
    "A.5.13": "Labelling of information",
    "A.5.14": "Information transfer",
    "A.5.15": "Access control",
    "A.5.16": "Identity management",
    "A.5.17": "Authentication information",
    "A.5.18": "Access rights",
    "A.5.19": "Information security in supplier relationships",
    "A.5.20": "Addressing information security within supplier agreements",
    "A.5.21": "Managing information security in the ICT supply chain",
    "A.5.22": "Monitoring, review and change management of supplier services",
    "A.5.23": "Information security for use of cloud services",
    "A.5.24": "Information security incident management planning and preparation",
    "A.5.25": "Assessment and decision on information security events",
    "A.5.26": "Response to information security incidents",
    "A.5.27": "Learning from information security incidents",
    "A.5.28": "Collection of evidence",
    "A.5.29": "Information security during disruption",
    "A.5.30": "ICT readiness for business continuity",
    "A.5.31": "Legal, statutory, regulatory and contractual requirements",
    "A.5.32": "Intellectual property rights",
    "A.5.33": "Protection of records",
    "A.5.34": "Privacy and protection of PII",
    "A.5.35": "Independent review of information security",
    "A.5.36": "Compliance with policies, rules and standards for information security",
    "A.5.37": "Documented operating procedures",
    # A.6 People (8)
    "A.6.1": "Screening",
    "A.6.2": "Terms and conditions of employment",
    "A.6.3": "Information security awareness, education and training",
    "A.6.4": "Disciplinary process",
    "A.6.5": "Responsibilities after termination or change of employment",
    "A.6.6": "Confidentiality or non-disclosure agreements",
    "A.6.7": "Remote working",
    "A.6.8": "Information security event reporting",
    # A.7 Physical (14)
    "A.7.1": "Physical security perimeters",
    "A.7.2": "Physical entry",
    "A.7.3": "Securing offices, rooms and facilities",
    "A.7.4": "Physical security monitoring",
    "A.7.5": "Protecting against physical and environmental threats",
    "A.7.6": "Working in secure areas",
    "A.7.7": "Clear desk and clear screen",
    "A.7.8": "Equipment siting and protection",
    "A.7.9": "Security of assets off-premises",
    "A.7.10": "Storage media",
    "A.7.11": "Supporting utilities",
    "A.7.12": "Cabling security",
    "A.7.13": "Equipment maintenance",
    "A.7.14": "Secure disposal or re-use of equipment",
    # A.8 Technological (34)
    "A.8.1": "User endpoint devices",
    "A.8.2": "Privileged access rights",
    "A.8.3": "Information access restriction",
    "A.8.4": "Access to source code",
    "A.8.5": "Secure authentication",
    "A.8.6": "Capacity management",
    "A.8.7": "Protection against malware",
    "A.8.8": "Management of technical vulnerabilities",
    "A.8.9": "Configuration management",
    "A.8.10": "Information deletion",
    "A.8.11": "Data masking",
    "A.8.12": "Data leakage prevention",
    "A.8.13": "Information backup",
    "A.8.14": "Redundancy of information processing facilities",
    "A.8.15": "Logging",
    "A.8.16": "Monitoring activities",
    "A.8.17": "Clock synchronization",
    "A.8.18": "Use of privileged utility programs",
    "A.8.19": "Installation of software on operational systems",
    "A.8.20": "Networks security",
    "A.8.21": "Security of network services",
    "A.8.22": "Segregation of networks",
    "A.8.23": "Web filtering",
    "A.8.24": "Use of cryptography",
    "A.8.25": "Secure development life cycle",
    "A.8.26": "Application security requirements",
    "A.8.27": "Secure system architecture and engineering principles",
    "A.8.28": "Secure coding",
    "A.8.29": "Security testing in development and acceptance",
    "A.8.30": "Outsourced development",
    "A.8.31": "Separation of development, test and production environments",
    "A.8.32": "Change management",
    "A.8.33": "Test information",
    "A.8.34": "Protection of information systems during audit testing",
}

ISO_THEMES = {"A.5": "Organizational", "A.6": "People", "A.7": "Physical", "A.8": "Technological"}

MANAGEMENT_CLAUSES = {
    "Cl.4": "Context of the organization",
    "Cl.5": "Leadership",
    "Cl.6": "Planning (incl. risk assessment & treatment)",
    "Cl.7": "Support (resources, competence, awareness)",
    "Cl.8": "Operation",
    "Cl.9": "Performance evaluation (monitoring, internal audit, management review)",
    "Cl.10": "Improvement (nonconformity & corrective action)",
}

# ---- Base mapping: CSF 2.0 category -> ISO refs ------------------------------------
CATEGORY_MAPPING = {
    "GV.OC": ["Cl.4", "A.5.31"],
    "GV.RM": ["Cl.6", "A.5.4"],
    "GV.RR": ["A.5.2", "A.5.3", "A.5.4", "Cl.5"],
    "GV.PO": ["A.5.1", "Cl.5"],
    "GV.OV": ["Cl.9", "A.5.35", "A.5.36"],
    "GV.SC": ["A.5.19", "A.5.20", "A.5.21", "A.5.22", "A.5.23"],
    "ID.AM": ["A.5.9", "A.5.12"],
    "ID.RA": ["Cl.6", "A.5.7", "A.8.8"],
    "ID.IM": ["Cl.10", "A.5.27"],
    "PR.AA": ["A.5.15", "A.5.16", "A.5.17", "A.5.18"],
    "PR.AT": ["A.6.3"],
    "PR.DS": ["A.8.24", "A.5.33", "A.8.13"],
    "PR.PS": ["A.8.9", "A.8.19", "A.8.8"],
    "PR.IR": ["A.8.20", "A.7.5", "A.8.14"],
    "DE.CM": ["A.8.16", "A.8.15"],
    "DE.AE": ["A.5.25", "A.8.16"],
    "RS.MA": ["A.5.24", "A.5.26"],
    "RS.AN": ["A.5.25", "A.5.28"],
    "RS.CO": ["A.6.8", "A.5.5"],
    "RS.MI": ["A.5.26"],
    "RC.RP": ["A.5.29", "A.5.30", "A.8.13"],
    "RC.CO": ["A.5.5", "A.5.6"],
}

# ---- Subcategory-level overrides (finer precision than the category default) -------
SUBCATEGORY_OVERRIDES = {
    # Govern
    "GV.OC-03": ["A.5.31", "A.5.34", "Cl.4"],
    "GV.OC-05": ["A.5.19", "A.5.21", "Cl.4"],
    "GV.RR-02": ["A.5.2", "Cl.5"],
    "GV.RR-04": ["A.6.1", "A.6.2", "A.6.5"],
    "GV.PO-01": ["A.5.1", "Cl.5"],
    "GV.PO-02": ["A.5.1", "Cl.9", "Cl.10"],
    "GV.SC-04": ["A.5.19", "A.5.9"],
    "GV.SC-05": ["A.5.20"],
    "GV.SC-06": ["A.5.19", "A.5.21"],
    "GV.SC-07": ["A.5.22"],
    "GV.SC-10": ["A.5.22", "A.6.5"],
    # Identify
    "ID.AM-01": ["A.5.9", "A.8.1"],
    "ID.AM-02": ["A.5.9"],
    "ID.AM-03": ["A.5.9", "A.8.20"],
    "ID.AM-04": ["A.5.9", "A.5.19"],
    "ID.AM-05": ["A.5.9", "A.5.12"],
    "ID.AM-07": ["A.5.12", "A.5.13"],
    "ID.AM-08": ["A.5.11", "A.7.14", "A.8.10"],
    "ID.RA-01": ["A.8.8", "Cl.6"],
    "ID.RA-02": ["A.5.7"],
    "ID.RA-05": ["Cl.6"],
    "ID.RA-06": ["Cl.6"],
    "ID.RA-08": ["A.8.8", "A.5.6"],
    "ID.RA-09": ["A.5.21", "A.8.30"],
    # Protect
    "PR.AA-01": ["A.5.16", "A.5.17"],
    "PR.AA-02": ["A.5.16"],
    "PR.AA-03": ["A.8.5", "A.5.17"],
    "PR.AA-05": ["A.5.15", "A.5.18", "A.8.2", "A.8.3"],
    "PR.AA-06": ["A.7.1", "A.7.2", "A.7.3"],
    "PR.AT-01": ["A.6.3"],
    "PR.AT-02": ["A.6.3"],
    "PR.DS-01": ["A.8.24", "A.5.33"],
    "PR.DS-02": ["A.5.14", "A.8.24"],
    "PR.DS-10": ["A.7.7", "A.8.12"],
    "PR.DS-11": ["A.8.13"],
    "PR.PS-01": ["A.8.9"],
    "PR.PS-02": ["A.8.8", "A.8.19"],
    "PR.PS-03": ["A.7.13"],
    "PR.PS-04": ["A.8.15"],
    "PR.PS-05": ["A.8.19", "A.8.7"],
    "PR.PS-06": ["A.8.25", "A.8.28"],
    "PR.IR-01": ["A.8.20", "A.8.22"],
    "PR.IR-02": ["A.7.5", "A.7.11"],
    "PR.IR-03": ["A.8.14"],
    "PR.IR-04": ["A.8.6"],
    # Detect
    "DE.CM-01": ["A.8.16", "A.8.20"],
    "DE.CM-02": ["A.7.4"],
    "DE.CM-03": ["A.8.16", "A.8.15"],
    "DE.CM-06": ["A.5.22", "A.8.16"],
    "DE.CM-09": ["A.8.16", "A.8.7"],
    "DE.AE-02": ["A.5.25", "A.8.16"],
    "DE.AE-07": ["A.5.7"],
    "DE.AE-08": ["A.5.25"],
    # Respond
    "RS.MA-01": ["A.5.24", "A.5.26"],
    "RS.MA-02": ["A.5.25"],
    "RS.AN-03": ["A.5.27"],
    "RS.AN-06": ["A.5.28"],
    "RS.AN-07": ["A.5.28"],
    "RS.CO-02": ["A.5.5", "A.6.8"],
    "RS.CO-03": ["A.6.8"],
    # Recover
    "RC.RP-01": ["A.5.29", "A.5.30"],
    "RC.RP-03": ["A.8.13"],
    "RC.CO-03": ["A.5.6"],
    "RC.CO-04": ["A.5.5", "A.5.6"],
}


def iso_ref_title(ref):
    """Return the human title for an ISO Annex A control or management clause ref."""
    if ref in ISO_CONTROLS:
        return ISO_CONTROLS[ref]
    if ref in MANAGEMENT_CLAUSES:
        return MANAGEMENT_CLAUSES[ref]
    return "(unknown ref)"


def theme_of(ref):
    if ref in MANAGEMENT_CLAUSES:
        return "ISMS Clause"
    return ISO_THEMES.get(ref.rsplit(".", 1)[0], "Other")


def mapping_for(subcat_id):
    """ISO refs for a CSF subcategory: override if present, else the category default."""
    if subcat_id in SUBCATEGORY_OVERRIDES:
        return SUBCATEGORY_OVERRIDES[subcat_id]
    cat = subcat_id.rsplit("-", 1)[0]
    return CATEGORY_MAPPING.get(cat, [])


if __name__ == "__main__":
    assert len(ISO_CONTROLS) == 93, f"expected 93 controls, got {len(ISO_CONTROLS)}"
    from collections import Counter
    themes = Counter(theme_of(c) for c in ISO_CONTROLS)
    print("ISO 27001:2022 Annex A controls:", len(ISO_CONTROLS), dict(themes))
    assert themes["Organizational"] == 37 and themes["People"] == 8
    assert themes["Physical"] == 14 and themes["Technological"] == 34
    print("All control refs in mappings are valid:",
          all(r in ISO_CONTROLS or r in MANAGEMENT_CLAUSES
              for refs in list(CATEGORY_MAPPING.values()) + list(SUBCATEGORY_OVERRIDES.values())
              for r in refs))
    print("OK")
