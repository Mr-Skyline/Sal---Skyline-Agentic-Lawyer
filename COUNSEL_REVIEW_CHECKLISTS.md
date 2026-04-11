# State Lien & Deadline Reference — Counsel Review Checklists

**Status:** Reference material for counsel sign-off. NOT legal advice. Each section summarizes key statutory provisions for the state's mechanics lien / construction payment framework relevant to Skyline Painting operations. Counsel must verify, approve, and sign off before any deadline-related content appears in production prompts or automated workflows.

---

## Colorado (CO) — C.R.S. § 38-22-101 et seq.

### Key deadlines
- **Notice of Intent to Lien:** 10 business days before filing (C.R.S. § 38-22-109(3))
- **Lien Statement filing:** Within 4 months after last furnishing of labor/materials (C.R.S. § 38-22-109(5))
- **Enforcement (lawsuit):** Within 6 months after lien statement filing (C.R.S. § 38-22-110)

### Key provisions
- Applies to improvements to real property
- Subcontractors and suppliers must serve a Notice of Intent before filing
- General contractor can file without prior NTI in most cases
- Residential projects may have additional notice requirements

### Counsel checklist
- [ ] Verified NTI timing and service method for Skyline's typical role (GC vs sub)
- [ ] Confirmed lien statement content requirements per § 38-22-109
- [ ] Reviewed 6-month enforcement window and tolling scenarios
- [ ] Approved any CO-specific language in Sal prompts

---

## Florida (FL) — Ch. 713, Florida Statutes

### Key deadlines
- **Notice to Owner (NTO):** Within 45 days of first furnishing (§ 713.06) — subcontractors/suppliers only
- **Claim of Lien recording:** Within 90 days after last furnishing (§ 713.08)
- **Enforcement (lawsuit):** Within 1 year of recording (§ 713.22)
- **Contractor's Final Affidavit:** Required before final payment (§ 713.06(3)(d))

### Key provisions
- NTO is critical for subcontractors — no NTO, no lien rights
- Owner's "Notice of Commencement" must be recorded before work begins
- Conditional and unconditional waivers/releases recognized (§ 713.20)
- Fraudulent lien filing carries penalties (§ 713.31)

### Counsel checklist
- [ ] Verified NTO timing for Skyline as subcontractor vs GC
- [ ] Confirmed 90-day claim of lien recording window
- [ ] Reviewed waiver/release form requirements
- [ ] Approved any FL-specific language in Sal prompts

---

## Arizona (AZ) — A.R.S. § 33-981 et seq.

### Key deadlines
- **Preliminary 20-Day Notice:** Within 20 days of first furnishing (§ 33-992.01) — subcontractors/suppliers
- **Lien recording:** Within 120 days after completion (§ 33-993(A))
- **Enforcement (lawsuit):** Within 6 months of recording (§ 33-998)

### Key provisions
- 20-Day Notice must be served on owner, GC, and construction lender
- "Completion" defined in § 33-993 (final inspection, occupancy, or cessation of work)
- Residential projects: additional notice and disclosure requirements
- Owner can demand a "Release of Lien" bond to remove lien from property

### Counsel checklist
- [ ] Verified 20-Day Notice requirements for Skyline's role
- [ ] Confirmed completion definition applicable to painting contracts
- [ ] Reviewed 120-day recording + 6-month enforcement timeline
- [ ] Approved any AZ-specific language in Sal prompts

---

## Texas (TX) — Property Code Ch. 53

### Key deadlines
- **Monthly notices:** Subcontractors/suppliers must send monthly notices by 15th of 2nd month after labor/materials furnished (§ 53.056)
- **Lien affidavit filing:** By 15th of 4th month after last month of work (§ 53.052) — for GCs; by 15th of 3rd month for subs (§ 53.057)
- **Enforcement (lawsuit):** Within 1 year for residential, 2 years for commercial (§ 53.158)

### Key provisions
- Texas uses a "fund trapping" system — notices trap funds in the owner's hands
- Retainage rules: 10% retainage required for certain contracts
- Residential projects: additional consumer protection notices
- "Inception of work" date is critical for priority

### Counsel checklist
- [ ] Verified monthly notice requirements for Skyline's role
- [ ] Confirmed affidavit filing deadlines (GC vs sub timelines differ)
- [ ] Reviewed fund-trapping mechanics and retainage rules
- [ ] Approved any TX-specific language in Sal prompts

---

## Nebraska (NE) — R.R.S. Neb. § 52-101 et seq.

### Key deadlines
- **Lien filing:** Within 120 days after last furnishing (§ 52-137)
- **Enforcement (lawsuit):** Within 2 years of filing (§ 52-101)
- **Notice to owner (residential):** Before filing on residential property (§ 52-137.01)

### Key provisions
- No preliminary notice requirement for commercial projects
- Residential projects: must serve written notice on owner before filing
- Service of lien by personal service or certified mail within 10 days of filing
- Owner may demand a lien release bond

### Counsel checklist
- [ ] Verified 120-day filing window for Skyline's work type
- [ ] Confirmed residential notice requirement applicability
- [ ] Reviewed service-of-lien requirements (10 days post-filing)
- [ ] Approved any NE-specific language in Sal prompts

---

## Retention Policy

### Current state
- **No auto-delete** of matter files, correspondence archives, or review exports
- Manual retention only — files persist until explicitly removed by an authorized operator
- Supabase metadata rows (correspondence_threads, skyline_review_exports) persist indefinitely

### Counsel checklist
- [ ] Approved written retention policy duration (e.g., 7 years post-matter-close)
- [ ] Approved destruction procedure (who authorizes, what gets deleted, audit trail)
- [ ] Confirmed embedding vectors follow same retention as source documents
- [ ] Reviewed PII handling in archives (redaction before external share)

---

## Sign-off tracker

| State/Topic | Counsel reviewed | Date | Notes |
|-------------|-----------------|------|-------|
| Colorado (CO) | ☐ | | |
| Florida (FL) | ☐ | | |
| Arizona (AZ) | ☐ | | |
| Texas (TX) | ☐ | | |
| Nebraska (NE) | ☐ | | |
| Retention policy | ☐ | | |
