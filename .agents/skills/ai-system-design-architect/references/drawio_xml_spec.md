# Draw.io Multi-Page XML Specification & Generation Guide

This guide defines how to construct valid, importable Draw.io XML files for Enterprise AI System Architecture diagrams. All style strings are production-tested and extracted from verified reference diagrams.

---

## 1. Multi-Page File Envelope

A `.drawio` file uses the `<mxfile>` root containing one `<diagram>` per page. Use **850×1100** (letter portrait) for dense views and **1600×1000** (landscape) for wide logical views.

Every page must start with the two mandatory base cells `id="0"` and `id="1"`.

```xml
<mxfile host="app.diagrams.net" version="24.0.0" pages="10">

  <diagram id="LogicalView" name="1. Logical Architecture">
    <mxGraphModel dx="1600" dy="1000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1600" pageHeight="1000" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <!-- nodes & edges -->
      </root>
    </mxGraphModel>
  </diagram>

  <diagram id="InfraMultiRegion" name="2. Infrastructure (Multi-Region)">
    <mxGraphModel dx="1247" dy="775" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1600" pageHeight="1000" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
      </root>
    </mxGraphModel>
  </diagram>

  <diagram id="InfraRegionDetail" name="3. Infrastructure (Region Detail)">
    <mxGraphModel dx="987" dy="465" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="850" pageHeight="1100" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
      </root>
    </mxGraphModel>
  </diagram>

  <diagram id="DataArch" name="4. Data Architecture">
    <mxGraphModel grid="1" page="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" pageScale="1" pageWidth="1600" pageHeight="1000" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
      </root>
    </mxGraphModel>
  </diagram>

  <diagram id="MLOpsView" name="5. MLOps CI-CD Pipelines">
    <mxGraphModel grid="1" page="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" pageScale="1" pageWidth="1600" pageHeight="1000" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
      </root>
    </mxGraphModel>
  </diagram>

  <diagram id="ModelServing" name="6. Model Serving Architecture">
    <mxGraphModel dx="1419" dy="587" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1100" pageHeight="750" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
      </root>
    </mxGraphModel>
  </diagram>

  <diagram id="SecurityView" name="7. Security &amp; Governance">
    <mxGraphModel grid="1" page="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" pageScale="1" pageWidth="1400" pageHeight="1000" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
      </root>
    </mxGraphModel>
  </diagram>

  <diagram id="MonitoringView" name="8. Monitoring &amp; Operations">
    <mxGraphModel dx="1645" dy="775" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1600" pageHeight="850" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
      </root>
    </mxGraphModel>
  </diagram>

  <diagram id="DataPrivacyView" name="9. Data Privacy &amp; Governance">
    <mxGraphModel grid="1" page="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" pageScale="1" pageWidth="1600" pageHeight="1000" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
      </root>
    </mxGraphModel>
  </diagram>

  <diagram id="GovernanceHITL" name="10. AI Safety &amp; HITL Review">
    <mxGraphModel grid="1" page="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" pageScale="1" pageWidth="1600" pageHeight="1000" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
      </root>
    </mxGraphModel>
  </diagram>

</mxfile>
```

---

## 2. Native Cloud Provider Icon Catalog

Always use native cloud icons on Infrastructure pages. **Never use generic rounded rectangles for cloud services.**

> **MCP Tip**: Use the draw.io MCP `search_shapes` tool to discover exact style strings for any icon:
> `search_shapes("aws eks")`, `search_shapes("azure sql")`, `search_shapes("gcp bigquery")`.
> The MCP server searches ~10,000 shapes and returns copy-paste ready style strings.
> **Prefer MCP-returned styles** over the tables below when available -- they are always up to date.

### 2.1 AWS Resource Icons

Base pattern (apply to every AWS icon):

```
outlineConnect=0;fontColor=#232F3E;gradientColor=none;strokeColor=none;dashed=0;
verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;
aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.<SERVICE>;
fillColor=<FILL>;
```

| Service | `resIcon` value | `fillColor` |
|---------|----------------|-------------|
| EKS | `mxgraph.aws4.eks` | `#ED7100` |
| EC2 | `mxgraph.aws4.ec2` | `#ED7100` |
| Lambda | `mxgraph.aws4.lambda` | `#ED7100` |
| S3 | `mxgraph.aws4.s3` | `#3F8624` |
| RDS | `mxgraph.aws4.rds` | `#2E27AD` |
| API Gateway | `mxgraph.aws4.api_gateway` | `#E7157B` |
| SageMaker | `mxgraph.aws4.sagemaker` | `#01A88D` |
| CloudFront | `mxgraph.aws4.cloudfront` | `#8C4FFF` |
| Internet Gateway | `mxgraph.aws4.internet_gateway` | `#8C4FFF` |
| NAT Gateway | `mxgraph.aws4.nat_gateway` | `#8C4FFF` |
| ELB / ALB | `mxgraph.aws4.elastic_load_balancing` | `#8C4FFF` |
| CloudWatch | `mxgraph.aws4.cloudwatch` | `#E7157B` |
| CloudWatch Logs | `mxgraph.aws4.cloudwatch_logs` | `#E7157B` |
| Transit Gateway | `mxgraph.aws4.transit_gateway` | `#8C4FFF` |
| VPC Endpoints | `mxgraph.aws4.vpc_endpoints` | `#8C4FFF` |
| Direct Connect | `mxgraph.aws4.direct_connect` | `#8C4FFF` |
| Route Table | `mxgraph.aws4.route_table` | `#8C4FFF` |
| Security Group | `mxgraph.aws4.security_group` | `#DD3522` |
| Network ACL | `mxgraph.aws4.network_access_control_list` | `#8C4FFF` |
| MSK (Kafka) | `mxgraph.aws4.managed_streaming_for_kafka` | `#ED7100` |

Additional AWS shapes (not `resourceIcon`):

| Shape | `style` pattern | `fillColor` |
|-------|----------------|-------------|
| Client | `shape=mxgraph.aws4.client;outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#232F3E;strokeColor=none;` | `#232F3E` |
| Internet | `shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.internet_alt2;fillColor=#232F3E;strokeColor=#FFFFFF;` | `#232F3E` |
| Corporate DC | `shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.corporate_data_center;fillColor=#232F3E;strokeColor=#FFFFFF;` | `#232F3E` |
| General Cloud | `shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.general_AWS_cloud;fillColor=#232F3E;strokeColor=none;` | `#232F3E` |

XML example — an EKS icon:

```xml
<mxCell id="eks_1" value="EKS Cluster" style="outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#ED7100;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.eks;" vertex="1" parent="1">
  <mxGeometry x="30" y="40" width="60" height="60" as="geometry" />
</mxCell>
```

### 2.2 Azure Service Icons

Base pattern (SVG image reference):

```
aspect=fixed;html=1;points=[];align=center;image;fontSize=11;
image=img/lib/azure2/<CATEGORY>/<SERVICE>.svg;
verticalLabelPosition=bottom;verticalAlign=top;
```

| Service | Category / File |
|---------|----------------|
| AKS (Kubernetes) | `containers/Kubernetes_Services.svg` |
| Azure ML | `ai_machine_learning/Machine_Learning.svg` |
| Azure SQL | `databases/SQL_Database.svg` |
| Cosmos DB | `databases/Azure_Cosmos_DB.svg` |
| Azure Functions | `compute/Function_Apps.svg` |
| Blob Storage | `storage/Storage_Accounts.svg` |
| App Gateway | `networking/Application_Gateways.svg` |

XML example — Azure AKS icon:

```xml
<mxCell id="aks_1" value="AKS Cluster" style="aspect=fixed;html=1;points=[];align=center;image;fontSize=11;image=img/lib/azure2/containers/Kubernetes_Services.svg;verticalLabelPosition=bottom;verticalAlign=top;" vertex="1" parent="1">
  <mxGeometry x="30" y="40" width="60" height="60" as="geometry" />
</mxCell>
```

### 2.3 GCP Service Icons

Base pattern (SVG image reference):

```
aspect=fixed;html=1;points=[];align=center;image;fontSize=11;
image=img/lib/google/<CATEGORY>/<SERVICE>.svg;
verticalLabelPosition=bottom;verticalAlign=top;
```

| Service | Category / File |
|---------|----------------|
| GKE | `containers/Kubernetes_Engine.svg` |
| BigQuery | `analytics/BigQuery.svg` |
| Cloud Spanner | `databases/Cloud_Spanner.svg` |
| Cloud Functions | `serverless/Cloud_Functions.svg` |
| Pub/Sub | `event/Cloud_PubSub.svg` |
| Cloud Storage | `storage_databases/Cloud_Storage.svg` |
| Cloud Load Balancer | `networking/Cloud_Load_Balancing.svg` |

XML example — GKE icon:

```xml
<mxCell id="gke_1" value="GKE Cluster" style="aspect=fixed;html=1;points=[];align=center;image;fontSize=11;image=img/lib/google/containers/Kubernetes_Engine.svg;verticalLabelPosition=bottom;verticalAlign=top;" vertex="1" parent="1">
  <mxGeometry x="30" y="40" width="60" height="60" as="geometry" />
</mxCell>
```

---

## 3. Cloud / VPC / Subnet Group Shapes

Infrastructure diagrams must use provider-native group shapes for cloud boundaries, VPCs, and subnets. These enable nested container layouts.

### 3.1 AWS Group Shapes

All AWS groups share a common `points` prefix for connection anchors:

```
points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=0;
```

Append one of these suffixes:

| Boundary | Style suffix (append to common prefix) |
|----------|---------------------------------------|
| **AWS Cloud** | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_aws_cloud_alt;stroke=#FF9900;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#FF9900;dashed=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;strokeWidth=2;` |
| **AWS Cloud (Named)** | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_aws_cloud;stroke=#232F3E;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;spacingTop=5;dashed=0;fontSize=14;fontStyle=1;` |
| **Region** | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_region;stroke=#147EBA;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;spacingTop=5;dashed=1;fontSize=13;fontStyle=1;` |
| **VPC** | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc;stroke=#248814;fillColor=#E8F5E9;verticalAlign=top;align=left;spacingLeft=30;spacingTop=5;dashed=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;` |
| **Public Subnet** | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;grStroke=0;stroke=#248814;fillColor=#E9F3E6;verticalAlign=top;align=left;spacingLeft=30;spacingTop=5;dashed=0;fontSize=11;fontStyle=1;` |
| **Private Subnet** | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;grStroke=0;stroke=#DF8600;fillColor=#FFF2CC;verticalAlign=top;align=left;spacingLeft=30;spacingTop=5;dashed=0;fontSize=11;fontStyle=1;` |
| **Database Subnet** | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;grStroke=0;stroke=#DD3522;fillColor=#FFCCCC;verticalAlign=top;align=left;spacingLeft=30;spacingTop=5;dashed=0;fontSize=11;fontStyle=1;` |

**Availability Zone** boundary (simple dashed rect — not a group shape):

```
fillColor=none;strokeColor=#147EBA;dashed=1;verticalAlign=top;fontStyle=1;fontColor=#147EBA;fontSize=12;whiteSpace=wrap;html=1;
```

### 3.2 Azure Group Shapes

| Boundary | Key style differences |
|----------|----------------------|
| **Azure Cloud** | Same points prefix + `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_aws_cloud_alt;stroke=#0078D4;fillColor=none;fontColor=#0078D4;` |
| **VNet** | Same points prefix + `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc;stroke=#0078D4;fillColor=#E3F2FD;fontColor=#0078D4;` |

### 3.3 GCP Group Shapes

| Boundary | Key style differences |
|----------|----------------------|
| **GCP Cloud** | Same points prefix + `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_aws_cloud_alt;stroke=#4285F4;fillColor=none;fontColor=#4285F4;` |
| **VPC** | Same points prefix + `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc;stroke=#4285F4;fillColor=#E8F0FE;fontColor=#4285F4;` |

### 3.4 Cloud Header Badge Inside Group

Place a text cell as the first child of a cloud group:

```xml
<mxCell id="aws_header" value="AWS Cloud" style="text;html=1;fontSize=18;fontStyle=1;align=center;verticalAlign=middle;fillColor=#FF9900;strokeColor=none;fontColor=#FFFFFF;rounded=1;arcSize=20;" vertex="1" parent="aws_cloud">
  <mxGeometry x="100" y="10" width="170" height="35" as="geometry" />
</mxCell>
```

Replace `fillColor=#FF9900` with `#0078D4` for Azure or `#4285F4` for GCP.

---

## 4. Container Nesting with Parent Hierarchy

The `parent` attribute places a cell inside a container. Child coordinates are **relative to the parent's origin**, not the canvas.

```xml
<!-- Level 1: AWS Cloud on canvas root -->
<mxCell id="aws_cloud" value="" style="...group_aws_cloud_alt;stroke=#FF9900;..." vertex="1" parent="1">
  <mxGeometry x="20" y="170" width="370" height="380" as="geometry" />
</mxCell>

  <!-- Level 2: VPC inside AWS Cloud -->
  <mxCell id="aws_vpc" value="" style="...group_vpc;stroke=#248814;fillColor=#E8F5E9;..." vertex="1" parent="aws_cloud">
    <mxGeometry x="15" y="55" width="340" height="310" as="geometry" />
  </mxCell>

    <!-- Level 3: VPC label text inside VPC -->
    <mxCell id="vpc_label" value="VPC 10.0.0.0/16" style="text;html=1;fontSize=11;fontStyle=0;align=left;verticalAlign=top;fillColor=none;strokeColor=none;fontColor=#248814;" vertex="1" parent="aws_vpc">
      <mxGeometry x="35" y="5" width="120" height="20" as="geometry" />
    </mxCell>

    <!-- Level 3: EKS Cluster inside VPC -->
    <mxCell id="eks_node" value="EKS Cluster" style="outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#ED7100;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.eks;" vertex="1" parent="aws_vpc">
      <mxGeometry x="30" y="40" width="60" height="60" as="geometry" />
    </mxCell>

    <!-- Level 3: S3 inside VPC -->
    <mxCell id="s3_node" value="S3 Data Lake" style="outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#3F8624;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.s3;" vertex="1" parent="aws_vpc">
      <mxGeometry x="200" y="40" width="60" height="60" as="geometry" />
    </mxCell>
```

**Critical rules:**
- A container cell must have `container=1` in its style (AWS group shapes include this implicitly).
- Edges between cells in different containers: set `parent="1"` on the edge and reference the cell IDs directly. Draw.io resolves cross-container edges automatically.
- Never duplicate `id="0"` or `id="1"` — these are reserved base cells.

---

## 5. Edge Labels as Child Cells

Every major edge should have a descriptive label. Labels are separate `<mxCell>` elements with `connectable="0"` and `parent` set to the edge's ID.

### 5.1 Standard Labeled Edge

```xml
<!-- The edge -->
<mxCell id="e1" edge="1" source="src_id" target="tgt_id" parent="1" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#333333;strokeWidth=2;endArrow=blockThin;endFill=1;">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
<!-- The label (child of the edge) -->
<mxCell id="e1_label" connectable="0" parent="e1" value="Raw Events &amp; Data" style="edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];fontSize=10;fontColor=#333333;" vertex="1">
  <mxGeometry relative="1" x="-0.1" as="geometry">
    <mxPoint as="offset" />
  </mxGeometry>
</mxCell>
```

- `x="-0.1"` shifts the label slightly toward the source. Use `x="0"` for center, `x="0.3"` toward target.
- Add `fillColor=#ffffff;rounded=1;` to the label style for a background pill effect (useful in busy diagrams).

### 5.2 Cross-Cloud VPN / Interconnect Edge

```xml
<mxCell id="vpn_edge" edge="1" source="aws_cloud" target="azure_cloud" parent="1" value="VPN / ExpressRoute" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#E91E63;strokeWidth=3;dashed=0;fontColor=#E91E63;fontSize=11;fontStyle=1;labelBackgroundColor=#FFFFFF;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
```

### 5.3 Edge Style Variants

| Semantics | Style additions |
|-----------|----------------|
| **Primary flow** | `strokeWidth=2;dashed=0;` |
| **Optional / backup** | `strokeWidth=1;dashed=1;` |
| **Replication** | `strokeWidth=2;dashed=1;fontSize=10;fontStyle=2;` + label "Replication" |
| **Cross-cloud** | `strokeWidth=3;fontStyle=1;labelBackgroundColor=#FFFFFF;` |
| **Color by layer** | Match `strokeColor` to source layer color (see Visual Quality Standards) |
| **Bidirectional** | `endArrow=blockThin;endFill=1;startArrow=blockThin;startFill=1;` |

---

## 6. Specialized Shape Catalog

Use domain-appropriate shapes — never plain rectangles for databases, files, or decisions.

### 6.1 Database Cylinder

```xml
<mxCell id="db_1" value="PostgreSQL" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=10;fillColor=#ffffff;strokeColor=#7b1fa2;strokeWidth=1;fontSize=10;shadow=1;" vertex="1" parent="1">
  <mxGeometry x="200" y="140" width="100" height="55" as="geometry" />
</mxCell>
```

### 6.2 Document Shape (Files)

```xml
<mxCell id="doc_1" value="Files (CSV/JSON)" style="shape=document;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=0.15;fillColor=#FFFFFF;strokeColor=#6c8ebf;fontSize=11;" vertex="1" parent="1">
  <mxGeometry x="45" y="265" width="150" height="40" as="geometry" />
</mxCell>
```

### 6.3 Table Shape (Dimension / Fact Tables)

```xml
<mxCell id="tbl_1" value="Dimension Tables" style="shape=table;startSize=20;container=0;collapsible=0;childLayout=tableLayout;fontSize=11;fillColor=#FFFFFF;strokeColor=#b85450;" vertex="1" parent="1">
  <mxGeometry x="940" y="230" width="120" height="40" as="geometry" />
</mxCell>
```

### 6.4 Decision Diamond (Approval Gates)

```xml
<mxCell id="gate_1" value="Approval&#xa;Gate" style="shape=mxgraph.flowchart.decision;fillColor=#ef4444;fontColor=#ffffff;strokeColor=#dc2626;fontSize=10;fontStyle=1;whiteSpace=wrap;html=1;shadow=1;" vertex="1" parent="1">
  <mxGeometry x="920" y="205" width="80" height="60" as="geometry" />
</mxCell>
```

### 6.5 UML Actor (Users / Personas)

```xml
<mxCell id="user_1" value="Users" style="shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fillColor=#1565c0;strokeColor=#0d47a1;fontColor=#1a237e;fontStyle=1;fontSize=12;" vertex="1" parent="1">
  <mxGeometry x="70" y="690" width="50" height="80" as="geometry" />
</mxCell>
```

### 6.6 Kubernetes Icon

```xml
<mxCell id="k8s_1" value="Kubernetes&#xa;Cluster" style="shape=mxgraph.kubernetes.icon2;fillColor=#326ce5;fontColor=#ffffff;strokeColor=#1e4d9e;fontSize=10;fontStyle=1;whiteSpace=wrap;html=1;rounded=1;shadow=1;prIcon=node;" vertex="1" parent="1">
  <mxGeometry x="1170" y="200" width="85" height="50" as="geometry" />
</mxCell>
```

### 6.7 Display Shape (Dashboards)

```xml
<mxCell id="dash_1" value="Monitoring&#xa;Dashboard" style="shape=mxgraph.flowchart.display;fillColor=#f59e0b;fontColor=#ffffff;strokeColor=#d97706;fontSize=11;fontStyle=1;whiteSpace=wrap;html=1;shadow=1;" vertex="1" parent="1">
  <mxGeometry x="1350" y="120" width="150" height="55" as="geometry" />
</mxCell>
```

### 6.8 Process Block (Pipeline Stages)

```xml
<mxCell id="proc_1" value="CI Pipeline" style="shape=mxgraph.flowchart.process;fillColor=#10b981;fontColor=#ffffff;strokeColor=#059669;fontSize=12;fontStyle=1;whiteSpace=wrap;html=1;rounded=1;shadow=1;" vertex="1" parent="1">
  <mxGeometry x="315" y="130" width="150" height="50" as="geometry" />
</mxCell>
```

### 6.9 Layered Rectangle (BI Dashboards)

```xml
<mxCell id="bi_1" value="BI Dashboards&#xa;(Tableau / Power BI)" style="shape=mxgraph.general.layered_rect;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#666666;fontSize=11;" vertex="1" parent="1">
  <mxGeometry x="1250" y="150" width="160" height="45" as="geometry" />
</mxCell>
```

### 6.10 Actor Shape (Personas with Descriptions)

```xml
<mxCell id="persona_1" value="👤 External Users&#xa;&amp; Partners" style="shape=actor;whiteSpace=wrap;html=1;fillColor=#e1bee7;strokeColor=#7b1fa2;fontSize=11;fontStyle=1;" vertex="1" parent="1">
  <mxGeometry x="55" y="796" width="120" height="80" as="geometry" />
</mxCell>
```

---

## 7. Visual Styling Patterns

### 7.1 Container Recipe (3 Parts)

Every architectural layer container follows this pattern:

**Part A — Outer container rectangle:**
```
rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#43a047;strokeWidth=2;arcSize=8;
```

**Part B — Colored header badge (first child inside container):**
```
text;html=1;fontSize=14;fontStyle=1;align=center;verticalAlign=middle;fillColor=#43a047;strokeColor=none;fontColor=#ffffff;rounded=1;arcSize=20;
```

**Part C — Inner service cards:**
```
rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#43a047;strokeWidth=1;fontSize=11;fontStyle=0;arcSize=12;shadow=1;
```

XML example (Application Layer container):

```xml
<!-- Outer container -->
<mxCell id="app_layer" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#43a047;strokeWidth=2;arcSize=8;dashed=0;" vertex="1" parent="1">
  <mxGeometry x="190" y="670" width="200" height="430" as="geometry" />
</mxCell>
<!-- Header badge -->
<mxCell id="app_header" value="Banking Applications" style="text;html=1;fontSize=14;fontStyle=1;align=center;verticalAlign=middle;fillColor=#43a047;strokeColor=none;fontColor=#ffffff;rounded=1;arcSize=20;" vertex="1" parent="1">
  <mxGeometry x="200" y="680" width="180" height="30" as="geometry" />
</mxCell>
<!-- Inner card with emoji -->
<mxCell id="app_card_1" value="🏦 Retail Banking&#xa;Portal" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#43a047;strokeWidth=1;fontSize=11;fontStyle=0;arcSize=12;shadow=1;" vertex="1" parent="1">
  <mxGeometry x="210" y="725" width="160" height="50" as="geometry" />
</mxCell>
```

### 7.2 Page Title

Every page must have a bold title:

```xml
<mxCell id="title" value="AI Platform Architecture" style="text;html=1;fontSize=24;fontStyle=1;align=center;verticalAlign=middle;fillColor=none;strokeColor=none;fontColor=#1a237e;" vertex="1" parent="1">
  <mxGeometry x="400" y="20" width="500" height="40" as="geometry" />
</mxCell>
```

### 7.3 Layer Legend Badges

Color-coded layer identifiers displayed in a legend row:

```xml
<mxCell id="legend_app" value="Application Layer" style="text;html=1;fontSize=12;fontStyle=1;align=center;verticalAlign=middle;fillColor=#e8f5e9;strokeColor=#a5d6a7;rounded=1;arcSize=10;fontColor=#2e7d32;" vertex="1" parent="1">
  <mxGeometry x="210" y="630" width="160" height="30" as="geometry" />
</mxCell>
```

### 7.4 Full-Width Governance / Infrastructure Bars

Horizontal bars spanning the full diagram width for cross-cutting concerns:

```xml
<mxCell id="gov_bar" value="Data Governance &amp; Quality  |  Catalog  |  Lineage  |  Access Control  |  Data Quality" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;fontSize=12;fontStyle=1;arcSize=8;shadow=1;" vertex="1" parent="1">
  <mxGeometry x="20" y="670" width="1420" height="50" as="geometry" />
</mxCell>
```

### 7.5 Emoji Usage in Service Cards

Prefix card labels with relevant emojis for quick visual scanning:

```
🏦 Retail Banking Portal        🔐 Authentication & Authorization
📱 Mobile Banking App           ⚡ Rate Limiting & Throttling
💼 Corporate Banking            🔄 Request Routing
🤖 AI Chatbot Interface         📊 Observability (Tracing, Metrics)
🧠 Fraud Detection Model        🗄️ Data Lake (S3 / HDFS)
📈 Credit Scoring               🔍 AML/KYC Compliance AI
🔒 mTLS Encryption              🛡️ WAF & DDoS Protection
🚀 A/B Testing & Deployment     📋 Audit Trail & Compliance
```

### 7.6 Dashed Outer Wrapper for Logical Grouping

For MLOps stages or pipeline phases that do not need container nesting:

```
rounded=1;whiteSpace=wrap;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=11;fontStyle=1;verticalAlign=top;spacingTop=5;dashed=1;dashPattern=5 5;opacity=60;
```

---

## 8. ID Naming & Cross-Page Rules

### 8.1 ID Scope

Each `<diagram>` in a `.drawio` file has its own independent ID namespace. Cell IDs only need to be unique **within their page**. The same ID can appear on different pages without conflict.

### 8.2 Naming Conventions

Use one of these patterns:

- **Prefixed descriptive**: `p1_eks_cluster`, `p2_vpc_main`, `p3_rds_primary`
- **Random (draw.io native)**: `OxpIIuvBopeIrIHy80Nz-1`, `32uvmKtEX-A14SYFZzL0-5`

Either works. Be consistent within a page.

### 8.3 Mandatory Base Cells

Every page must include:

```xml
<mxCell id="0" />
<mxCell id="1" parent="0" />
```

All top-level nodes use `parent="1"`. Nested children use `parent="<container_id>"`.

### 8.4 Edge Reference Integrity

- `source` and `target` on an edge must reference cell IDs **on the same page**.
- `parent` on an edge label must reference the edge's ID **on the same page**.
- If an edge crosses containers (e.g., a resource in VPC-A to a resource in VPC-B), set `parent="1"` on the edge itself.

### 8.5 Geometry Rules

- Top-level cells: `x` / `y` are absolute canvas coordinates.
- Nested cells (with `parent="<container>"`): `x` / `y` are **relative to the parent container's top-left corner**.
- Edges use `relative="1"` geometry. Edge labels use `relative="1"` with optional `x` offset (-1.0 to 1.0).
- For edges with waypoints, use `<Array as="points">` with `<mxPoint>` children.

```xml
<mxCell id="e2" edge="1" source="a" target="b" parent="1" style="edgeStyle=orthogonalEdgeStyle;rounded=1;">
  <mxGeometry relative="1" as="geometry">
    <Array as="points">
      <mxPoint x="410" y="360" />
      <mxPoint x="410" y="360" />
    </Array>
  </mxGeometry>
</mxCell>
```
