# School access roles

CampusFlow supports two school membership roles:

- **Manager** can read, create, and correct school records.
- **Viewer** can read school records and reports but cannot create or change marks.

Both roles still require a Django staff account, and every request remains scoped to that account's single school membership. Set each role in Django admin under **School memberships**. Existing memberships are migrated as managers to preserve access; newly created memberships also default to manager for compatibility, so administrators should choose Viewer when a read-only account is needed.

This is a basic permission boundary, not a full school identity system. Before handling real student data, add school-owned onboarding and access review, test account removal and audit retention, and complete the privacy/legal review.
