# AI Solution Architecture - Problem Statements & System Designs

This directory contains problem statements, business requirements, architectural designs, and Draw.io diagrams for enterprise AI solutions.

---

## 📂 Directory Structure

```
designs/
├── README.md                           # Directory overview & guidelines
├── templates/
│   ├── problem_statement_template.md  # Template for specifying business problem statements & requirements
│   └── system_design_template.md      # Template for documenting AI system architecture designs
└── examples/
    └── enterprise-rag/
        ├── problem_statement.md        # Sample problem statement for Enterprise RAG
        └── system_design.md           # Sample system design following the 10-view architecture standard
```

---

## 🚀 How to Add a New AI System Design

1. Create a new subfolder under `designs/` (e.g. `designs/my-use-case/`).
2. Copy `designs/templates/problem_statement_template.md` to `designs/my-use-case/problem_statement.md` and describe your requirements.
3. Use the **ai-system-design-architect** skill to generate the complete system design and Draw.io XML file.
4. Save the generated design in `designs/my-use-case/system_design.md` and export the `.drawio` diagram file.
