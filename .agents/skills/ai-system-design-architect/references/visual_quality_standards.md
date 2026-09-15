# Visual Quality Standards & Layout Recipes

Reference for color palettes, cloud provider branding, and per-view spatial layout specifications. All colors are extracted from the validated reference file `ref_project_finance.drawio`.

---

## 1. Material Design Color Palette by Architectural Layer

Use these exact hex values to maintain visual consistency across all diagram pages.

| Layer | Container Fill | Container Stroke | Header Badge Fill | Card Stroke | Edge Color |
|---|---|---|---|---|---|
| Presentation / Users | `#e8eaf6` | `#9fa8da` | `#1565c0` | `#1565c0` | `#1565c0` |
| Application | `#e8f5e9` | `#a5d6a7` | `#43a047` | `#43a047` | `#43a047` |
| Gateway | `#fff3e0` | `#ffcc80` | `#ef6c00` | `#ef6c00` | `#ef6c00` |
| Service Mesh | `#fce4ec` | `#f48fb1` | `#c62828` | `#c62828` | `#c62828` |
| AI / ML | `#e1f5fe` | `#81d4fa` | `#0277bd` | `#0277bd` | `#0277bd` |
| Data | `#f3e5f5` | `#ce93d8` | `#7b1fa2` | `#7b1fa2` | `#7b1fa2` |
| MLOps | `#e0f2f1` | `#80cbc4` | `#00695c` | `#00695c` | `#00695c` |
| Infrastructure | `#eceff1` | `#b0bec5` | `#455a64` | `#455a64` | `#455a64` |
| Security - IAM | `#dae8fc` | `#6c8ebf` | `#1a73e8` | `#0d47a1` | `#0d47a1` |
| Security - Policy | `#fff2cc` | `#d6b656` | `#f9a825` | `#f57f17` | `#f57f17` |
| Security - Audit | `#d5e8d4` | `#82b366` | `#2e7d32` | `#2e7d32` | `#2e7d32` |
| Security - Threat | `#f8cecc` | `#b85450` | `#e53935` | `#c62828` | `#c62828` |
| Monitoring - Collection | `#e8f5e9` | `#388e3c` | `#4caf50` | `#388e3c` | `#388e3c` |
| Monitoring - Visualization | `#e3f2fd` | `#1565c0` | `#1e88e5` | `#1565c0` | `#1565c0` |
| Monitoring - Alerting | `#fff3e0` | `#e65100` | `#fb8c00` | `#e65100` | `#e65100` |
| Monitoring - Operations | `#f3e5f5` | `#6a1b9a` | `#8e24aa` | `#6a1b9a` | `#6a1b9a` |

**Inner card defaults**: `fillColor=#ffffff` (white background), stroke color from the layer's Card Stroke column above, `shadow=1`, `arcSize=12`.

**Header badge defaults**: Fill from Header Badge column, `strokeColor=none`, `fontColor=#ffffff`, `rounded=1;arcSize=20`.

---

## 2. Cloud Provider Brand Colors

| Provider | Cloud Boundary Stroke | Cloud Header Badge | VPC/VNet Fill | VPC Stroke | Edge Color |
|---|---|---|---|---|---|
| AWS | `#FF9900` | `#FF9900` bg, `#FFFFFF` text | `#E8F5E9` | `#248814` | `#FF9900` |
| Azure | `#0078D4` | `#0078D4` bg, `#FFFFFF` text | `#E3F2FD` | `#0078D4` | `#0078D4` |
| GCP | `#4285F4` | `#4285F4` bg, `#FFFFFF` text | `#E8F0FE` | `#4285F4` | `#4285F4` |
| Cross-Cloud Links | `#E91E63` | N/A | N/A | N/A | `#E91E63` (`strokeWidth=3`, `fontStyle=1`) |

---

## 3. Per-View Layout Specifications

### View 1: Logical Architecture

- **Canvas**: `pageWidth="1600" pageHeight="1100"`
- **Layout**: Left-to-right layered columns OR top-to-bottom horizontal bands.
- **Key shapes**: Color-coded container rectangles (`rounded=1;strokeWidth=2;arcSize=8`) with header badges. Inner service cards (`shadow=1;arcSize=12`). UML actors (`shape=umlActor`) on the far left for Users, Admins, API Consumers. Horizontal bars at the bottom for MLOps and Infrastructure/Security.
- **Minimum components**: 6 layer containers, 25+ inner service cards, 3+ actor shapes.
- **Spatial recipe**: Actors at x=20-100. Vertical layer containers spaced ~200px apart starting at x=190. Each container ~200px wide, ~430px tall. MLOps bar at y=1140, full width. Infrastructure bar at y=1300, full width. Legend chips at top between title and first row.

### View 2: Infrastructure (Multi-Cloud)

- **Canvas**: `pageWidth="1600" pageHeight="800"`
- **Layout**: Three cloud provider groups arranged side-by-side horizontally.
- **Key shapes**: AWS group shapes (`mxgraph.aws4.group`) for cloud boundaries and VPCs. Native provider icons for services. Labeled cross-cloud edges (`strokeWidth=3;strokeColor=#E91E63`) for VPN/ExpressRoute/Interconnect. Terraform/Monitoring bar across the top.
- **Minimum components**: 3 cloud groups, VPC nested inside each, 6+ service icons per cloud, 2+ cross-cloud links.
- **Spatial recipe**: IaC/Monitoring bar at y=70 (width=600, dashed). Cloud groups at y=170, each ~370px wide, spaced ~15px apart. VPC nested at offset (15, 55) inside each cloud. Resource icons inside VPC at relative positions.

### View 3: Infrastructure (Region Detail)

- **Canvas**: `pageWidth="1600" pageHeight="1300"`
- **Layout**: Nested containment: AWS Cloud > Region > VPC > Availability Zones (2 columns) > Subnet tiers stacked vertically.
- **Key shapes**: AWS group shapes for Cloud, Region, VPC. Subnet groups color-coded: Public (green `#E9F3E6`), Private (yellow `#FFF2CC`), Database (red `#FFCCCC`). AWS resource icons for IGW, NAT Gateway, ALB, EC2, RDS, Route Tables, Security Groups, NACLs, Transit Gateway, Direct Connect, VPC Endpoints, S3. Replication edges (dashed, labeled).
- **Minimum components**: 2 Availability Zones, 3 subnet tiers per AZ, 12+ networking/compute resources, Internet/Users icon at top, On-Premises icon at left.
- **Spatial recipe**: Internet icon at top center (y=110). IGW below (y=230). AZ columns side by side (x=210, x=800), each ~530px wide. Public subnets at y=370, Private at y=570, Database at y=820 within each AZ. NAT Gateways inside public subnets. Transit Gateway at far left (x=130), VPC Endpoints at far right (x=1390).

### View 4: Data Architecture

- **Canvas**: `pageWidth="1600" pageHeight="800"`
- **Layout**: Left-to-right horizontal pipeline with labeled inter-stage edges.
- **Key shapes**: Container rectangles for each stage. Cylinder shapes (`shape=cylinder3`) for databases and data lake zones. Kafka icon (`mxgraph.aws4.managed_streaming_for_kafka`). Document shapes for file sources. Bronze/Silver/Gold cylinders stacked vertically (use fill colors: Bronze `#e6d0b8`, Silver `#C0C0C0`, Gold `#FFD700`). Processing layer container below the lake. Governance and Monitoring bars at the bottom spanning full width.
- **Minimum components**: 6 pipeline stages (Sources, Ingestion, Lake, Processing, Warehouse, Consumption), 15+ inner components. Labeled edges between every stage.
- **Spatial recipe**: Data Sources at x=20 (200px wide). Ingestion at x=290. Data Lake at x=560 (260px wide). Warehouse at x=900. Consumption at x=1220. Processing layer below the lake at y=450. Governance bar at y=670. Monitoring bar at y=735.

### View 5: MLOps CI/CD Pipeline

- **Canvas**: `pageWidth="1600" pageHeight="600"`
- **Layout**: Left-to-right 6-stage pipeline with a dashed feedback loop returning from Monitoring back to Source Control.
- **Key shapes**: Dashed container rectangles for stage groupings (`dashed=1;dashPattern=5 5;opacity=60`). Cylinder for Model Registry and Feature Store. Decision diamond (`shape=mxgraph.flowchart.decision`) for Approval Gates. GitHub icon shape for Git. Flowchart process shapes for CI/CD pipelines. Bold labeled edges between stages (Push/PR, Trigger, Register, Deploy, Telemetry). Feedback loop edge (`dashed=1;dashPattern=8 4;strokeColor=#ef4444`) from Monitoring to Source Control. Data Pipeline sub-section at bottom.
- **Minimum components**: 6 stage containers, 20+ inner components, feedback loop.
- **Spatial recipe**: Stage containers each ~220px wide, spaced at x=20, 280, 540, 800, 1060, 1320. Stage height ~280px at y=80. Data Pipeline bar at y=460 spanning full width.

### View 6: Model Serving

- **Canvas**: `pageWidth="1200" pageHeight="800"`
- **Layout**: Left-to-right request flow with KServe inference service as a central dashed container.
- **Key shapes**: Client shape (`mxgraph.aws4.client`). AWS API Gateway icon. ELB icon. Dashed container for KServe inference service enclosing Transformer, Predictor, Explainer (stacked vertically), and Autoscaler. Cylinder for Feature Store and Model Registry on the right. GPU Cluster icon below-right. Monitoring and Logging icons at the bottom. A/B Testing component. Labeled edges for every connection (REST/gRPC, Auth & Rate Limit, Features, Load Model, Compute, Metrics, Logs, Traffic Split).
- **Minimum components**: 10+ components with labeled edges.
- **Spatial recipe**: Client at x=60. API Gateway at x=220. Load Balancer at x=380. KServe box (280px wide) at x=500, y=120. Feature Store at x=870, y=150. Model Registry at x=870, y=270. GPU Cluster at x=870, y=420. Monitoring/Logging at y=530.

### View 7: Security & Governance

- **Canvas**: `pageWidth="1300" pageHeight="1000"`
- **Layout**: 4-quadrant layout with a Governance Dashboard bar at the bottom center.
- **Key shapes**: Rounded container rectangles for each quadrant (color-coded per palette). Cylinder for Audit Logs. Actor shapes for External/Internal users. Labeled dashed edges for cross-quadrant interactions ("enforces", "triggers", "feeds"). Legend box in bottom-left corner with color swatches.
- **Minimum components**: 4 quadrant containers, 20+ inner components, Governance Dashboard bar, Legend, 2 actor shapes.
- **Spatial recipe**: Top-Left (IAM, blue): x=55, y=106, 520x280. Top-Right (Policy, yellow): x=615, y=106, 580x280. Bottom-Left (Monitoring, green): x=55, y=416, 520x240. Bottom-Right (Threat, red): x=615, y=416, 580x240. Governance bar at y=696, centered, 700px wide. Legend at x=55, y=696, 190x180. Actors at bottom corners y=796.

### View 8: Monitoring & Operations

- **Canvas**: `pageWidth="1400" pageHeight="800"`
- **Layout**: 4 horizontal rows stacked vertically, each representing a layer.
- **Key shapes**: Layer title text cells with emoji on the left side of each row. Colored rounded rectangles for each tool/component. Edges flowing top-to-bottom between layers. Dashed edges for secondary/optional connections.
- **Minimum components**: 4 layer rows, 20+ components spread across rows (5-6 per row).
- **Spatial recipe**: Collection Layer at y=95 (green family). Visualization Layer at y=285 (blue family). Alerting Layer at y=475 (orange family). Operations Layer at y=665 (purple family). Components within each row spread from x=100 to x=1350, spaced ~200px apart.

### View 9: Data Lineage & Privacy Governance

- **Canvas**: `pageWidth="1400" pageHeight="800"`
- **Layout**: Top-to-bottom flow showing data lineage from raw source to generated output, with privacy controls as side-panel overlays.
- **Key shapes**: Document shapes for raw sources. Rounded rectangles for processing steps (PII Detection, Masking, Chunking, Embedding). Cylinder for Vector Store. Dashed boundary containers for tenant isolation zones. Audit trail cylinder on the side. Labeled edges describing data transformations at each step.
- **Minimum components**: 10+ components in the lineage flow, tenant isolation boundaries, audit trail.
- **Spatial recipe**: Raw sources at y=80. PII Detection at y=200. Masking at y=320. Chunking/Embedding at y=440. Vector Store at y=560. Response generation at y=680. Audit trail column at x=1100. Tenant isolation dashed boundary from y=300 to y=600.

### View 10: AI Model Governance, Safety & HITL

- **Canvas**: `pageWidth="1400" pageHeight="600"`
- **Layout**: Left-to-right pipeline with decision gates (diamond shapes) at key transition points.
- **Key shapes**: Rounded rectangles for evaluation engines (Ragas, TruLens). Decision diamonds (`shape=mxgraph.flowchart.decision`) for Approval Gates. Cylinder for Model Registry with stage labels (Experimental, Staging, Candidate, Production). Rounded rectangles for HITL Review Queue. Safety filter components on the side. Labeled edges for transitions (pass, fail, review, promote, reject).
- **Minimum components**: 10+ components including at least 2 decision diamond gates.
- **Spatial recipe**: Evaluation engines at x=50. First approval gate diamond at x=300. HITL review queue at x=500. Model Registry stages at x=700 (stacked or side-by-side). Production gate diamond at x=1000. Safety filters as a column at x=1200.
