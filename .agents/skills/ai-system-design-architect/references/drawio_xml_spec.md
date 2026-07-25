# Draw.io Multi-Page XML Specification & Generation Guide

This guide details how to construct valid, importable Draw.io XML files containing multiple diagram pages for Enterprise AI Systems.

---

## 1. Multi-Page File Structure (10 Views)

A multi-page `.drawio` file uses the `<mxfile>` root tag containing multiple `<diagram>` children:

```xml
<mxfile host="Electron" agent="Mozilla/5.0" version="24.0.0">
  <!-- Page 1: Logical View -->
  <diagram id="LogicalView" name="1. Logical Architecture">
    <mxGraphModel dx="1600" dy="1000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1600" pageHeight="1000" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <!-- Nodes & Edges -->
      </root>
    </mxGraphModel>
  </diagram>

  <!-- Page 2: Infrastructure View -->
  <diagram id="InfraView" name="2. Infrastructure Architecture">
    <mxGraphModel dx="1600" dy="1000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1600" pageHeight="1000" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <!-- Nodes & Edges -->
      </root>
    </mxGraphModel>
  </diagram>

  <!-- Page 3: Security View -->
  <diagram id="SecurityView" name="3. Security Architecture">
    <mxGraphModel dx="1600" dy="1000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1600" pageHeight="1000" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <!-- Nodes & Edges -->
      </root>
    </mxGraphModel>
  </diagram>

  <!-- Page 4: Observability View -->
  <diagram id="ObservabilityView" name="4. Observability & Monitoring">
    <mxGraphModel dx="1600" dy="1000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1600" pageHeight="1000" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <!-- Nodes & Edges -->
      </root>
    </mxGraphModel>
  </diagram>

  <!-- Page 5: CI/CD View -->
  <diagram id="CicdView" name="5. MLOps CI-CD Pipelines">
    <mxGraphModel dx="1600" dy="1000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1600" pageHeight="1000" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <!-- Nodes & Edges -->
      </root>
    </mxGraphModel>
  </diagram>

  <!-- Page 6: Data Privacy Governance -->
  <diagram id="DataPrivacyView" name="6. Data Privacy & Governance">
    <mxGraphModel dx="1600" dy="1000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1600" pageHeight="1000" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <!-- Nodes & Edges -->
      </root>
    </mxGraphModel>
  </diagram>

  <!-- Page 7: Resilience & LLM Fallback -->
  <diagram id="ResilienceView" name="7. HA & Multi-Provider Fallback">
    <mxGraphModel dx="1600" dy="1000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1600" pageHeight="1000" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <!-- Nodes & Edges -->
      </root>
    </mxGraphModel>
  </diagram>

  <!-- Page 8: Multi-Agent Orchestration -->
  <diagram id="MultiAgentView" name="8. Multi-Agent Orchestration">
    <mxGraphModel dx="1600" dy="1000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1600" pageHeight="1000" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <!-- Nodes & Edges -->
      </root>
    </mxGraphModel>
  </diagram>

  <!-- Page 9: FinOps Caching -->
  <diagram id="FinOpsView" name="9. FinOps & Semantic Cache">
    <mxGraphModel dx="1600" dy="1000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1600" pageHeight="1000" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <!-- Nodes & Edges -->
      </root>
    </mxGraphModel>
  </diagram>

  <!-- Page 10: Model Governance & HITL -->
  <diagram id="GovernanceHITLView" name="10. AI Safety & HITL Review">
    <mxGraphModel dx="1600" dy="1000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1600" pageHeight="1000" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <!-- Nodes & Edges -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

---

## 2. Cell Elements (`<mxCell>`)

Every page must start with the default base cells:
```xml
<mxCell id="0" />
<mxCell id="1" parent="0" />
```

### Vertices (Nodes)
```xml
<mxCell id="node_id" value="Label Text" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F1F5F9;strokeColor=#475569;fontColor=#0F172A;fontStyle=1;" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="160" height="70" as="geometry" />
</mxCell>
```

### Containers / Swimlanes
```xml
<mxCell id="group_id" value="Layer Name" style="swimlane;whiteSpace=wrap;html=1;fillColor=#F8FAFC;strokeColor=#CBD5E1;fontStyle=1;fontColor=#334155;startSize=30;rounded=1;" vertex="1" parent="1">
  <mxGeometry x="60" y="100" width="1480" height="150" as="geometry" />
</mxCell>
```

### Edges (Connectors)
```xml
<mxCell id="edge_id" value="Protocol / Label" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthoLoop=1;jettySize=auto;html=1;strokeColor=#3B82F6;strokeWidth=2;" edge="1" parent="1" source="source_node_id" target="target_node_id">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
```
