# Enterprise RAG Knowledge Assistant - Problem Statement

## 1. Executive Summary
The organization requires a secure, high-throughput Enterprise Knowledge Assistant capable of performing accurate Q&A over 500,000 internal documents (SOPs, technical specifications, policy docs, SharePoint pages) with sub-second response times and role-based access control.

---

## 2. Business Problem & Goals
- **Current State**: Employees spend 4.5 hours per week searching across fragmented document repositories.
- **Desired Future State**: A central conversational interface providing grounded answers with exact source citations.
- **Target KPIs**:
  - Reduction of document search time by 60%.
  - Response time < 1.5 seconds.
  - Zero hallucination on non-existent policy questions (faithful context grounding).

---

## 3. AI Use Case Classification
- **Domain**: Knowledge Retrieval & Generative AI.
- **Primary Pattern**: Hybrid RAG (Dense Embeddings + Sparse BM25 + Vector DB + NeMo Guardrails).

---

## 4. Key Requirements

### Functional Requirements
- Multi-format ingestion (PDF, DOCX, HTML, Markdown).
- Role-Based Access Control (RBAC) filtering so users only see answers sourced from documents they have permission to read.
- Source citation links in generated responses.

### Technical Constraints
- **Cloud**: AWS (us-east-1).
- **Scale**: 25,000 active employees, peak 200 req/sec.
- **Compliance**: GDPR, SOC2 Type II, PII redaction.
