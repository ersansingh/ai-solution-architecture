# Generative AI & LLM Problem Statement Template

> **Paradigm**: Generative AI & Large Language Models (RAG / SLMs / LLMs / Multi-Agent Orchestration / Fine-Tuning)  
> **Skill Reference**: `.agents/skills/ai-algorithm-selector/SKILL.md`

---

## 1. Business Objective & Problem Definition
* **Business Objective**: [Automate complex reasoning, document extraction, conversational support, code synthesis, or knowledge retrieval]
* **Target Use Case**: [e.g., Enterprise Document Q&A / Customer Support Agent / Automated Code Assistant / Contract Summarization]
* **Current Baseline**: [e.g., Human document search / Rule-based chatbot / Keyword search]

---

## 2. Generative Pattern & Model Selection Focus
* **Primary GenAI Pattern**:
  * [ ] Retrieval-Augmented Generation (RAG)
  * [ ] Fine-Tuned Small Language Model (SLM < 10B parameters)
  * [ ] Large Language Model API (GPT-4o / Claude 3.5 / DeepSeek-V3)
  * [ ] Autonomous AI Agent with Tool Execution
  * [ ] In-Context Learning & Few-Shot Prompting
* **Input Context & Documents**: [Unstructured PDFs, HTML docs, database schemas, API specs]
* **Output Format**: [Structured JSON schema / Markdown report / Multi-turn Dialogue / SQL query / Code block]

---

## 3. Operational & Cost Parameters
* **Context Window Requirements**: [Average input tokens per request, max context length e.g. 16k to 128k tokens]
* **Token Economics & Cloud Budget**: [Max acceptable cost per 1M tokens, daily token volume]
* **Deployment Sovereignty**: [Cloud API allowed (OpenAI/Anthropic) vs Strictly On-Prem / Air-Gapped Private Hosting]
* **Latency SLA**: [Time-To-First-Token (TTFT) < 500 ms, throughput > 30 tokens/sec]

---

## 4. Evaluation & Quality Metrics
* **RAG Evaluation Metrics**: [RAGAS Faithfulness, Answer Relevance, Context Precision, Context Recall]
* **Generation Quality Metrics**: [BLEU / ROUGE / Human Eval Pass@1 / LLM-as-a-Judge score]
* **Hallucination Tolerance**: [Zero-tolerance (Requires strict grounding and citations)]

---

## 5. Governance, Safety & Tools
* **Safety Guardrails**: [NeMo Guardrails / Llama Guard for PII filtering, prompt injection, toxicity detection]
* **Tool / API Integration**: [Function calling, Vector DB search, Web browsing, SQL execution]
