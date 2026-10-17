# Business Requirements Document (BRD)

## Automated Invoice-to-Purchase-Order Reconciliation and Anomaly Detection

- **Document type:** Business Requirements Document
- **System:** Invoice Reconciliation System
- **Primary users:** Finance, Accounts Payable, Procurement, and Audit teams
- **Processing mode:** Automated
- **Document source:** Google Drive
- **Reconciliation type:** Invoice versus Purchase Order (PO)
- **Frontend scope:** Excluded

---

## 1. Business Objective

The objective is to automate the reconciliation of supplier invoices against corresponding purchase orders using documents stored in Google Drive.

Invoices and purchase orders may be available as digitally generated PDFs, scanned PDFs, or image files.

The system must extract relevant financial information, identify corresponding purchase orders, compare invoice and PO details, detect discrepancies and potential anomalies, and produce traceable reconciliation results.

The system should reduce manual effort, improve financial accuracy, identify duplicate billing risks, and provide consistent evidence for financial review and audit.

## 2. Business Problem

Manual invoice reconciliation can be time-consuming and error-prone, particularly when documents arrive in different formats or contain inconsistent information.

Common problems include:

- Invoice references to missing or incorrect purchase orders.
- Differences between invoiced and ordered quantities.
- Invoice prices that differ from approved PO prices.
- Incorrect invoice totals, taxes, or discounts.
- Duplicate invoices or repeated billing.
- Supplier identity mismatches.
- Poor-quality scanned documents and missing information.
- Limited visibility into unresolved discrepancies.
- Inconsistent reconciliation decisions and inadequate audit trails.

The proposed system will automate document processing and reconciliation while identifying cases that require further investigation.

## 3. Business Scope

### 3.1 In scope

- Discovering invoices and purchase orders in authorized Google Drive locations.
- Processing supported PDF and image files.
- Extracting invoice and PO information.
- Validating extracted information.
- Matching invoices against purchase orders.
- Comparing line items and financial amounts.
- Detecting duplicates and financial discrepancies.
- Classifying reconciliation outcomes.
- Recording processing results and exceptions.
- Maintaining traceability to source documents.
- Supporting automated processing and safe reprocessing.
- Providing reconciliation results to authorized downstream systems through the existing backend API.

### 3.2 Out of scope

Unless separately approved, the system will not:

- Initiate payments or bank transfers.
- Post financial transactions directly to the general ledger.
- Approve supplier payments.
- Modify original invoices or purchase orders.
- Create or amend purchase orders.
- Replace the organization's accounting or ERP system.
- Automatically determine fraud.
- Implement frontend screens.
- Modify the existing API contract without approval.

## 4. Stakeholders

| Stakeholder | Responsibility |
|---|---|
| Finance / Accounts Payable | Define reconciliation policies and financial tolerances |
| Procurement | Confirm PO validity, supplier details, and purchasing rules |
| Finance Controller | Approve financial controls and exception policies |
| IT / Engineering | Maintain system integration, processing, and reliability |
| Information Security | Approve document access and data protection controls |
| Internal Audit | Define traceability and audit evidence requirements |
| Business Owner | Approve scope, success criteria, and operational policies |

## 5. Business Workflow

The system must support the following business process:

1. Discover eligible documents in authorized Google Drive folders.
2. Identify document type and validate document accessibility.
3. Extract structured information from invoices and purchase orders.
4. Validate mandatory fields and extraction reliability.
5. Identify the relevant PO for each invoice.
6. Compare supplier, currency, line items, quantities, prices, taxes, and totals.
7. Apply approved matching rules and tolerances.
8. Detect discrepancies, duplicate candidates, and other anomalies.
9. Assign a reconciliation outcome.
10. Store the result and supporting evidence.
11. Make the result available through the backend API.
12. Route unresolved or suspicious cases to the defined exception process.

> A record must not be marked successfully reconciled merely because a matching PO number was found.

## 6. Document Requirements

### 6.1 Supported document types

The initial scope includes:

- Digitally generated PDFs.
- Scanned PDFs.
- JPEG/JPG images.
- PNG images.

Other formats require explicit approval.

### 6.2 Invoice information

The system should extract, where available:

- Invoice number.
- Supplier name and identifier.
- Invoice date and due date.
- Purchase order number.
- Currency.
- Invoice line descriptions and identifiers.
- Quantities and unit prices.
- Discounts.
- Tax rates and amounts.
- Subtotal and total.
- Shipping and additional charges.

### 6.3 Purchase order information

The system should extract, where available:

- PO number.
- Supplier identity.
- PO date.
- Currency.
- Line-item descriptions and identifiers.
- Ordered quantities.
- Unit prices.
- Discounts and tax details.
- Approved PO total.
- PO status.
- Remaining quantities or amounts, where available.

Missing information must be identified explicitly. The system must not invent values for fields that cannot be extracted.

## 7. Business Requirements

**BR-01: Document discovery**
The system shall discover eligible invoice and PO documents in configured, authorized Google Drive locations.

**BR-02: Document classification**
The system shall distinguish invoices, purchase orders, credit notes, unsupported documents, and other approved document categories.

**BR-03: Data extraction**
The system shall extract required invoice and PO fields from supported PDFs and images.

**BR-04: Data validation**
The system shall validate mandatory fields, dates, currency, identifiers, numeric values, and financial totals before reconciliation.

**BR-05: PO identification**
The system shall identify candidate purchase orders using approved matching identifiers and validate supplier identity and PO eligibility.

**BR-06: Line-item reconciliation**
The system shall compare corresponding invoice and PO line items using approved matching rules.

**BR-07: Financial reconciliation**
The system shall compare quantities, unit prices, discounts, taxes, additional charges, and totals according to approved financial policies.

**BR-08: Anomaly detection**
The system shall identify defined discrepancies, potential duplicate invoices, repeated billing, inconsistent totals, and document-quality problems.

**BR-09: Reconciliation classification**
The system shall assign a result based on the approved business rules and the available evidence.

**BR-10: Duplicate processing prevention**
The system shall prevent repeated processing from creating duplicate reconciliation records or unintended duplicate financial effects.

**BR-11: Audit traceability**
The system shall preserve links to source documents, reconciliation results, processing timestamps, and relevant decision evidence.

**BR-12: Exception handling**
The system shall identify records that cannot be safely reconciled automatically and make them available for the approved exception-handling process.

**BR-13: Reprocessing**
The system shall support safe reprocessing of eligible documents when processing fails, source data changes, or an authorized rule update requires reassessment.

**BR-14: API integration**
The system shall expose or consume reconciliation information through the existing API contract. Any missing API capabilities must be documented and approved before implementation.

## 8. Reconciliation Rules

### 8.1 PO matching

The system should use the following checks:

1. Match the invoice PO reference to a valid PO.
2. Validate supplier identity.
3. Validate currency compatibility.
4. Verify that the PO is eligible for invoicing.
5. Match invoice lines to PO lines using approved identifiers.
6. Compare quantities, prices, and financial totals.
7. Apply approved tolerances.
8. Determine the reconciliation result.

If multiple POs are plausible candidates, the system must not select one arbitrarily.

### 8.2 Quantity comparison

Compare invoiced quantities against ordered quantities and any previously invoiced or remaining quantities available in the authoritative system.

The business must define how partial invoices, multiple invoices against one PO, returns, and credit notes are handled.

### 8.3 Price comparison

Compare invoice unit prices with the approved PO unit prices.

Differences beyond the approved tolerance must be classified as discrepancies.

### 8.4 Tax and total comparison

Validate the relationship between subtotal, discounts, tax, shipping, other charges, and invoice total.

Apply the organization's approved tax and rounding rules. Do not assume tax treatment is identical across suppliers or jurisdictions.

### 8.5 Currency comparison

Invoices and POs must use compatible currencies unless an approved currency conversion policy applies.

Amounts in different currencies must not be compared directly as if they were equivalent.

## 9. Anomaly Categories

The system shall identify the following categories where sufficient evidence exists.

| Category | Example |
|---|---|
| Missing PO | Invoice references a PO that cannot be found |
| Supplier mismatch | Invoice supplier differs from the PO supplier |
| Quantity discrepancy | Invoiced quantity exceeds permitted quantity |
| Price discrepancy | Invoice unit price exceeds the approved PO price |
| Total discrepancy | Invoice total differs beyond permitted tolerance |
| Tax discrepancy | Tax calculation or tax amount is inconsistent |
| Currency mismatch | Invoice and PO currencies differ |
| Duplicate invoice | The same invoice appears to have been submitted more than once |
| Repeated billing | A PO line or quantity may have been billed repeatedly |
| Data extraction issue | A critical field is missing or unreliable |
| Document inconsistency | Extracted totals conflict with line-item calculations |
| PO eligibility issue | PO is closed, cancelled, or otherwise ineligible |

An anomaly is an exception requiring interpretation, not proof of fraud.

## 10. Reconciliation Outcomes

The business should define and approve the final status model.

Proposed outcomes include:

- **Matched:** All required checks pass.
- **Matched within tolerance:** Differences are within explicitly approved tolerances.
- **Partially matched:** Some invoice lines or quantities match, while others remain unresolved.
- **Unmatched:** No eligible PO can be identified.
- **Discrepancy detected:** One or more required financial checks fail.
- **Duplicate suspected:** The invoice may duplicate an existing submission.
- **Extraction failed:** Required information cannot be extracted reliably.
- **Requires review:** The record cannot be safely resolved automatically.
- **Processing failed:** A technical failure prevents completion.

These are proposed business labels, not a requirement to introduce new backend enum values.

The system must distinguish document-processing status, reconciliation outcome, and anomaly status.

## 11. Automatic Processing Policy

The system shall automatically process documents and produce reconciliation results according to approved rules.

Automatic successful reconciliation is permitted only when all mandatory checks pass.

The system must not automatically approve cases involving:

- Ambiguous PO identification.
- Unreliable critical-field extraction.
- Unresolved supplier mismatches.
- Financial discrepancies exceeding approved limits.
- Suspected duplicate billing.
- Ineligible or cancelled purchase orders.
- Missing mandatory financial information.

Such cases must be classified according to the approved exception policy.

The system must not initiate payments or financial postings as a consequence of reconciliation unless separately authorized.

## 12. Business Controls and Audit Requirements

The system must provide traceability for each reconciliation decision.

Required evidence should include:

- Original document reference.
- Extracted invoice and PO values.
- Matching identifiers.
- Comparison results.
- Variance calculations.
- Applicable reconciliation rule.
- Anomaly codes and explanations.
- Processing timestamp.
- Rule version or policy version.
- Processing failures and reprocessing history.

Access to documents and reconciliation data must follow organizational authorization and data-retention policies.

## 13. Non-Functional Requirements

The system must meet approved requirements for:

- Processing throughput.
- Maximum document size and page count.
- Processing latency.
- Availability and recovery.
- Data retention.
- Security and access control.
- Audit retention.
- Idempotency.
- Retry and failure handling.
- Observability and operational monitoring.

Numerical service-level targets must be agreed with the business and engineering teams rather than invented.

## 14. Business Acceptance Criteria

The solution will be accepted when:

1. Eligible documents are discovered from authorized Drive locations.
2. Supported PDFs and images are processed.
3. Required fields are extracted or explicitly flagged as unavailable.
4. Invoice-to-PO matching follows approved rules.
5. Financial comparisons use approved currency and rounding policies.
6. Defined anomalies are detected and explained.
7. Ambiguous or unsafe cases are not automatically approved.
8. Duplicate processing does not create duplicate reconciliation records.
9. Results retain traceability to their source documents.
10. Reconciliation outcomes are available through the agreed API.
11. Failed processing can be investigated and safely retried.
12. Tests demonstrate expected behavior on representative matching and anomaly scenarios.
13. Business owners approve the final rules and acceptance results.

## 15. Business Decisions Requiring Approval

Before production deployment, stakeholders must approve:

- Matching identifiers.
- Amount, quantity, and date tolerances.
- Partial-invoicing rules.
- Multiple invoices against one PO.
- Duplicate detection policy.
- Treatment of credit notes and cancelled POs.
- Currency conversion policy, if applicable.
- Anomaly severity and exception routing.
- Automatic reconciliation eligibility.
- Data retention and audit requirements.
- Processing frequency and service-level targets.

These decisions are prerequisites for reliable automatic financial reconciliation.
