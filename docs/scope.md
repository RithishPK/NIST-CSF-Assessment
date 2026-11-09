# Assessment Scope

**Assessment framework:** NIST Cybersecurity Framework (CSF) 2.0
**Organisation (example):** Dreams Home Estate Stay — a small homestay /
estate-stay business in Kodagu (Coorg), Karnataka, India
**Assessment type:** Current-state maturity assessment with target profile
**Date:** 2026-11-01

> This is a worked example. Replace this scope with your own organisation's
> details and re-score the workbook.

## 1. Business context
A family-run homestay offering guest accommodation. Bookings come through online
travel platforms (OTAs) and direct enquiries; payments are taken online and
in person. The business depends heavily on its online reputation (review sites),
so both guest-data protection and service availability matter.

## 2. Assets in scope

| Category | Examples |
|---|---|
| Hardware | Front-desk PC, owner's laptop, staff smartphones, Wi-Fi router, CCTV NVR/DVR |
| Software & SaaS | Booking/property-management tool, email (Google Workspace), accounting app, OTA extranets |
| Data | Guest personal data (names, contact, ID-proof scans), booking records, payment references, staff records |
| Network | Shared Wi-Fi covering guests, office devices and CCTV |
| Suppliers | OTA platforms, payment gateway, internet service provider, cloud/email provider |

## 3. Key data types
- **Guest PII** — names, phone, email, address, government ID scans (collected at check-in)
- **Payment data** — references/UPI details (card data largely handled by the gateway)
- **Operational data** — bookings, occupancy, pricing
- **Staff data** — basic HR records

## 4. Relevant obligations
- **India DPDP Act, 2023** — the business is a data fiduciary for guest personal
  data; obligations include purpose limitation, security safeguards and breach
  notification.
- OTA and payment-gateway contractual security terms.

## 5. Primary threats considered
- Phishing / business-email compromise targeting the owner or front desk
- OTA account takeover (fraudulent bookings, payout redirection)
- Ransomware / data loss on the front-desk PC
- Theft or exposure of guest ID scans and personal data
- Service/availability loss from power or internet outages (common locally)

## 6. Target profile rationale
The target is **Tier 2–3 (Risk Informed → Repeatable)**, not Tier 4. For a small
business, aiming for "documented, consistent, policy-backed" basics across the
board is realistic and high-value; chasing "adaptive/measured" everywhere would
be over-engineering. Targets are set per subcategory in the workbook to reflect
this.

## 7. Out of scope
- Penetration testing / technical exploitation (this is a governance & maturity
  assessment, not a pentest)
- Physical security beyond IT-relevant controls
- Third parties' internal security (assessed only at the contract/interface level)
