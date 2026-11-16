# CampusFlow market research

**Checked:** 2026-11-17. Published prices are vendor list examples and may change. Review comments are user reports, not universal findings. This is desk research; no school buyer interviews or pilot validate demand yet.

## Target customer and problem

Small schools that need a low-scope, staff-only marks register and class-level summaries. The current repo is a Django API for recording marks, school-scoped staff access, CSV export and aggregate summaries. It is not a complete student information system: it has no admissions, attendance, fees, parent/student accounts or school self-service.

## Competitors

| Product | Public pricing / offer | Review-reported weakness | Evidence |
|---|---|---|---|
| [Fedena](https://fedena.com/pricing-and-plans) | Standard $999/year, Premium $1,399/year, Ultimate $1,699/year on its current pricing page | A G2 reviewer says the large feature set can feel overwhelming and first-time users need training; low sample size. | [Pricing](https://fedena.com/pricing-and-plans); [G2 reviews](https://www.g2.com/products/fedena/reviews) |
| [OpenEduCat](https://www.openeducat.org/pricing/) | Modular; G2 lists one-year plan from $444 for 25 users; exact configurations vary | G2 reviewers cite configuration/setup time, a learning curve, technical support needs, and extra customization/hosting costs. | [Pricing](https://www.openeducat.org/pricing/); [G2 reviews](https://www.g2.com/products/openeducat/reviews) |
| [Teachmint](https://www.teachmint.com/terms) | Institution pricing is communicated via platform/official order; G2 lists Teachmint X2 Pro hardware at ₹150,000, not a comparable SaaS school quote | G2 reviewer reports bugs can take hours to days to resolve, and says the product lacked a delete control for mistaken records. Evidence is mixed and covers a broader product. | [Terms](https://www.teachmint.com/terms); [G2 reviews](https://www.g2.com/products/teachmint-g2/reviews) |
| [Gradelink](https://gradelink.com/pricing-plans/) | Pricing calculator example: $106/month plus $275 one-time setup at 25 enrolled students; price scales by school size/add-ons | G2 review summaries mention clunky usability, limited customization/advanced scheduling, and add-on costs. | [Pricing](https://gradelink.com/pricing-plans/); [G2 category/reviews](https://www.g2.com/categories/school-management-software?open_modal_url=%2Fproducts%2Fadvanta-innovations-advanta-rapid-erp%2Fwishlists%3Fhost_path%3D%252Fproducts%252Fadvanta-innovations-advanta-rapid-erp%26source%3Dcategory&order=g2_score&source=category) |
| [PowerSchool SIS](https://www.powerschool.com/) | Quote/demo-led; no directly comparable public list price found | G2 reviewer themes include menu hunting, complexity for less common tasks, and slowness in some reports; large district product and buyer scope differs. | [Product](https://www.powerschool.com/); [G2 reviews](https://www.g2.com/products/powerschool-sis/reviews) |

## Positioning hypothesis

**CampusFlow is a deliberately small, school-scoped marks API with role limits, export accountability, and no student-facing accounts.** It may suit a school that wants to keep its existing workflow and add a safer marks/reporting service; this positioning needs interviews and a pilot before it becomes a sales claim.

## Buyer questions

1. Who owns marks data and who is authorized to view or correct it?
2. Which existing reports are slow, error-prone, or repeatedly copied?
3. Would a school adopt an API-only service, or does it require staff-facing screens and support?
4. Which retention, deletion, guardian notice, data residency, and incident-response terms are mandatory?
5. What procurement and budget cycle applies, and would the school pay for a narrow pilot?
