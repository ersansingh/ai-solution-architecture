# Enterprise AI Solution Architecture, Agent Skills & MCP Integration

Welcome to the **Enterprise AI Solution Architecture** repository! This repository provides an end-to-end framework, production-grade lab modules, custom AI agent skills, and Model Context Protocol (MCP) server integrations for designing, building, monitoring, and governing enterprise-grade Artificial Intelligence (AI), Machine Learning (ML), Retrieval-Augmented Generation (RAG), and Large Language Model (LLM) platforms.

---

## 🚀 Key Architectural Modules & Labs

### 🧠 [Lab 1: AI Algorithm & Model Selection](ai-solution-architecture/lab1-ai-algorithm-selection/)
A structured 15-section framework and 10-dimension evaluation matrix for analyzing business requirements and selecting optimal AI algorithms across Supervised, Unsupervised, Deep Learning, Reinforcement Learning, and Generative AI paradigms.
* **Lab 1.1**: [Customer Churn Prediction](ai-solution-architecture/lab1-ai-algorithm-selection/use-cases/lab1.1-customer-churn-prediction/) (GBDTs / XGBoost / LightGBM)
* **Lab 1.2**: [Dynamic Pricing Engine](ai-solution-architecture/lab1-ai-algorithm-selection/use-cases/lab1.2-dynamic-pricing-engine/) (Contextual Bandits / LinUCB / Offline RL)
* **Lab 1.3**: [Enterprise Contract Analysis RAG](ai-solution-architecture/lab1-ai-algorithm-selection/use-cases/lab1.3-enterprise-contract-rag/) (Hybrid Search + Reranker + LLMs)
* **Lab 1.4**: [Network Intrusion & Zero-Day Anomaly Detection](ai-solution-architecture/lab1-ai-algorithm-selection/use-cases/lab1.4-network-anomaly-detection/) (Extended Isolation Forest + VAE + UMAP)
* **Lab 1.5**: [High-Speed Industrial Defect Detection](ai-solution-architecture/lab1-ai-algorithm-selection/use-cases/lab1.5-industrial-defect-detection/) (YOLOv8 / RT-DETR Edge Vision)

---

### 🏛️ [Lab 2: Enterprise AI System Design & Architecture](ai-solution-architecture/lab2-ai-system-designs/)
Comprehensive enterprise architecture specs detailing the **10 Crucial Enterprise AI Views** (Logical, Infrastructure, Security, Observability, CI/CD Pipeline, Data Privacy Governance, High Availability & Fallback, Multi-Agent Orchestration, FinOps Caching, and Model Governance HITL) along with importable multi-page `.drawio` XML files.
* **Lab 2.1**: [Intelligent Data Processing (IDP)](ai-solution-architecture/lab2-ai-system-designs/lab2.1-intelligent-data-processing/)
* **Lab 2.2**: [Enterprise RAG Architecture](ai-solution-architecture/lab2-ai-system-designs/lab2.2-enterprise-rag/)
* **Lab 2.4**: [Enterprise SaaS AI Platform](ai-solution-architecture/lab2-ai-system-designs/lab2.4-saas-ai-platform/)
* **Lab 2.5**: [Multi-Cloud Financial AI Architecture](ai-solution-architecture/lab2-ai-system-designs/lab2.5-multi-cloud-finance/)
* **Lab 2.6**: [Multi-Region Banking AI Platform](ai-solution-architecture/lab2-ai-system-designs/lab2.6-multi-region-banking-ai-platform/)

---

### ⚙️ [Lab 5: Model Training, Serving & MLOps Automation](ai-solution-architecture/lab5-model-training-serving/)
Full lifecycle MLOps implementation built on AWS SageMaker:
* **Lab 5.1**: [SageMaker Customer Churn Pipeline](ai-solution-architecture/lab5-model-training-serving/lab5.1-aws-sagemaker/) featuring an 11-phase implementation guide, training data samples, hyperparameter tuning, model registry, container deployment, and automated retraining pipelines.

---

### 🛡️ [Lab 6: Multi-Cloud Enterprise AI Observability & Governance](ai-solution-architecture/lab6-observability-governance/)
Production-grade telemetry framework integrating the AWS Ecosystem, OpenTelemetry (OTel Gateway), Observe Inc. (for logs and trace datasets), Prometheus, and Grafana.
* **Lab 6.1**: [AWS 5-Part Observability Architecture](ai-solution-architecture/lab6-observability-governance/lab6.1-observability-aws/)
  * *Part 1*: Infrastructure & Compute Observability (NVIDIA DCGM GPU metrics, EKS pod health, ADOT daemonsets).
  * *Part 2*: Data & Feature Observability (AWS Deequ PySpark quality checks, Glue Schema Registry, SageMaker PSI feature drift).
  * *Part 3*: Model Performance Observability (SageMaker Data Capture, Ground-Truth join engine, Accuracy/Precision/Recall/F1/ECE scores).
  * *Part 4*: Generative AI & LLM Observability (Judge LLM RAG Groundedness/Recall/Precision, Bedrock Guardrails, Prompt Injection scanning, Token cost accounting).
  * *Part 5*: Business, Security, Compliance & Closed-Loop Remediation (AWS CloudTrail, Config, Macie PII, Cost/ROI metrics, Step Functions auto-rollback & retraining).
* **Lab 6.3**: [Multi-Cloud AI Observability Framework](ai-solution-architecture/lab6-observability-governance/lab6.3-enterprise-muti-cloud-ai-observability/) spanning AWS, Microsoft Azure, Google Cloud Platform (GCP), and On-Premises GPU clusters.

---

## 🤖 Custom Agent Skills (`.agents/skills/`)

This repository exposes specialized AI skills for AI coding assistants (Gemini CLI, Antigravity IDE, Cursor, Claude):

1. **`ai-algorithm-selector`** ([`SKILL.md`](ai-solution-architecture/.agents/skills/ai-algorithm-selector/SKILL.md)): Analyzes problem statements and outputs standard 15-section algorithm recommendation reports.
2. **`ai-system-design-architect`** ([`SKILL.md`](ai-solution-architecture/.agents/skills/ai-system-design-architect/SKILL.md)): Generates complete 10-view enterprise system designs, Terraform IaC, CI/CD YAML, and multi-page `.drawio` XML files.
3. **`ai-ml-observability-architect`** ([`SKILL.md`](ai-solution-architecture/.agents/skills/ai-ml-observability-architect/SKILL.md)): Generates multi-cloud OTel Gateway configurations, Observe Inc. OPAL queries, Prometheus alert rules, Grafana dashboards, and Step Functions remediation workflows.

---

## 🔌 Model Context Protocol (MCP) Integration

The repository includes root-level [`mcp.json`](ai-solution-architecture/mcp.json) and editor-level [`.vscode/mcp.json`](ai-solution-architecture/.vscode/mcp.json) configurations for:

- **Draw.io MCP Server** (`@drawio/mcp`): Programmatically renders, views, and modifies architecture diagrams.
- **GitHub MCP Server** (`@modelcontextprotocol/server-github`): Enables GitHub repository searches, pull request reviews, issue management, and code inspection.

### `mcp.json` / `.vscode/mcp.json` Configuration
```json
{
  "$schema": "https://json.schemastore.org/mcp-config.json",
  "mcpServers": {
    "drawio": {
      "command": "npx",
      "args": [
        "-y",
        "@drawio/mcp"
      ],
      "env": {}
    },
    "github": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-github"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${env:GITHUB_PERSONAL_ACCESS_TOKEN}"
      }
    }
  }
}
```

> **Security Note**: Environment variable expansion (`"${env:GITHUB_PERSONAL_ACCESS_TOKEN}"`) automatically extracts your token from Windows without hardcoding secret keys into git-tracked files.

---

## 🛠️ Gemini CLI Commands

Use the local `gemini` CLI command in your terminal to launch interactive AI sessions and inspect active MCP servers:

```bash
# Launch interactive Gemini CLI session
gemini

# List configured MCP servers
gemini mcp list

# Add a new MCP server
gemini mcp add github npx -y @modelcontextprotocol/server-github

# Enable or disable an MCP server
gemini mcp enable github
gemini mcp disable github
```

---

## 📂 Repository Directory Structure

```
ai-solution-architecture/
├── .agents/
│   └── skills/
│       ├── ai-algorithm-selector/             # Algorithm Selection Skill
│       ├── ai-system-design-architect/         # System Design & Draw.io Skill
│       └── ai-ml-observability-architect/      # Multi-Cloud Observability Skill
├── lab1-ai-algorithm-selection/
│   ├── templates/                             # Problem & Recommendation Templates
│   └── use-cases/                             # 5 Industry Machine Learning Use Cases
├── lab2-ai-system-designs/
│   ├── templates/                             # System Design Templates
│   └── lab2.1 - lab2.6/                       # Enterprise AI Architecture Designs & Diagrams
├── lab5-model-training-serving/
│   └── lab5.1-aws-sagemaker/                  # SageMaker MLOps Pipeline & Sample Data
├── lab6-observability-governance/
│   ├── lab6.1-observability-aws/              # 5-Part AWS Observability Implementation
│   └── lab6.3-enterprise-muti-cloud-ai-observability/ # Multi-Cloud AI Observability Framework
├── templates/
│   ├── cloud_architecture.drawio              # Cloud Architecture Draw.io Template
│   └── ai_rag_pipeline.drawio                 # RAG Pipeline Draw.io Template
├── .vscode/mcp.json                           # Editor MCP Configuration
├── mcp.json                                   # Root MCP Configuration
├── package.json                               # Dependencies (@drawio/mcp)
└── README.MD                                  # Main Documentation Guide
```

---

## 📜 License

MIT License.
