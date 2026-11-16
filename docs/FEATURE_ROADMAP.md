# CampusFlow feature roadmap

Impact and effort are estimates, not demand evidence. Competitor gaps are hypotheses based on [`MARKET_RESEARCH.md`](MARKET_RESEARCH.md). Use synthetic data until a school privacy review and written data-handling agreement exist.

| # | Feature | User problem solved | Competitor gap to test | Impact | Effort | Status |
|---:|---|---|---|---|---|---|
| 1 | Manager and read-only viewer roles | Staff need access without every account being able to change grades | Role boundaries can be opaque in broad ERP products | High | Medium | Implemented locally; school-scoped permission tests |
| 2 | One-call class overview summary | Staff have to make separate requests for average and pass counts | Larger SIS products expose many modules when a marks-only view may suffice | High | Low | Implemented locally; one aggregate query, tenant-scoped tests |
| 3 | School setup checklist and validation | An admin may leave staff without a school assignment | Large suites require onboarding/configuration | High | Medium | Planned |
| 4 | Term and class grouping | Records need a usable class/term context | Broad SIS workflows may be excessive for a narrow marks tool | High | Medium | Planned; requires buyer confirmation |
| 5 | Explicit correction and approval workflow | Mistyped marks need accountable review | User reviews report deletion/correction control concerns in some products | High | High | Planned; no change history should expose old values |
| 6 | Soft archive and restore | Schools need to remove inactive records from reports without irreversible deletion | Deletion controls are a trust concern | High | Medium | Planned; retention policy needed |
| 7 | CSV import dry-run | Schools want to migrate without duplicate or malformed rows | Import configuration can add setup cost | High | Medium | Planned |
| 8 | Report card PDF preview | Staff need a printable parent-facing result | Full ERP can require broader adoption for a single report | Medium | High | Planned; legal/privacy review first |
| 9 | Standards-based grade bands | Percentage alone does not match every school's grading scale | Fixed grading logic may not fit each school | Medium | Medium | Planned; school-configurable, audited |
| 10 | Low-cohort privacy suppression | Small groups can reveal an individual learner | Aggregate views still risk re-identification | High | Medium | Planned; thresholds require policy approval |
| 11 | Bilingual labels and date formats | Staff work in regional language/date conventions | Multi-module products can have hard-to-find settings | Medium | Medium | Planned |
| 12 | Export receipt with filters and expiry | Staff need to know what data was exported and when | CSV copies can become uncontrolled | High | Medium | Export history exists; expiry/retention unimplemented |
| 13 | Staff account recovery and school reassignment flow | Staff turnover can leave records inaccessible | Setup/administration can require vendor support | High | Medium | Planned; admin-only and auditable |
| 14 | OpenAPI schema and synthetic demo dataset | Integrators need a safe way to try endpoints | API setup needs developer support | Medium | Low | Planned |
| 15 | Health, backup and restore runbook | A school needs recovery evidence before real records | Free/demo hosting is not durable | High | Medium | Planned; managed DB and restore proof required |

## Implementation status

Feature 1 is implemented locally. Feature 2 is implemented in the current worktree and combines school-scoped aggregate metrics without returning names or record-level data. Remaining items stay planned until each has tests, docs, accessibility review where relevant, and a buyer-confirmed need. No live school data or customer is verified.
