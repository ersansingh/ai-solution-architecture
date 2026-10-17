"""Generates architecture.drawio (10 pages) for the Invoice Reconciliation system.

Run:  python generate_drawio.py
Output: architecture.drawio (same folder)
"""
import itertools
import math
import os
from xml.sax.saxutils import escape

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "architecture.drawio")

BLUE, TEAL, PURPLE, ORANGE, RED, GREY, GREEN, AMBER = (
    "#1565C0", "#00796B", "#6A1B9A", "#E65100", "#C62828", "#455A64", "#2E7D32", "#B26A00")
ICON_FILL = {  # AWS category colours
    "compute": "#ED7100", "storage": "#7AA116", "db": "#C925D1", "net": "#8C4FFF",
    "sec": "#DD344C", "ml": "#01A88D", "app": "#E7157B", "mgmt": "#E7157B", "dev": "#C925D1",
}


def q(s):
    return escape(str(s), {'"': "&quot;"})


class Page:
    def __init__(self, name, title, width=1700, height=1000):
        self.name, self.title, self.w, self.h = name, title, width, height
        self.n = itertools.count(2)
        self.cells, self.edges, self.keys = [], [], {}
        self.vertex_count = 0
        self.text(title, 30, 14, width - 60, 40, "fontSize=24;fontStyle=1;align=left;")

    def nid(self):
        return f"c{next(self.n)}"

    def vertex(self, value, style, x, y, w, h, parent="1", key=None):
        i = self.nid()
        self.cells.append(
            f'<mxCell id="{i}" value="{q(value)}" style="{style}" vertex="1" parent="{parent}">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        if key:
            assert key not in self.keys, f"duplicate key {key} on {self.name}"
            self.keys[key] = i
        return i

    def text(self, value, x, y, w, h, extra=""):
        return self.vertex(value, f"text;html=1;strokeColor=none;fillColor=none;whiteSpace=wrap;{extra}", x, y, w, h)

    def container(self, key, title, color, x, y, cols, items):
        """items: list of (key,label,kind) kind: c=card, d=database cylinder, a:<cat>:<icon>, x=decision diamond."""
        rows = max(1, math.ceil(len(items) / cols))
        w, h = cols * 170 + 20, 44 + rows * 90 + 8
        self.vertex("", f"rounded=1;arcSize=8;strokeWidth=2;strokeColor={color};fillColor={color};fillOpacity=7;", x, y, w, h)
        self.vertex(title, f"rounded=1;arcSize=20;fillColor={color};strokeColor=none;fontColor=#ffffff;fontStyle=1;fontSize=12;html=1;",
                    x + 10, y + 8, w - 20, 26)
        for idx, (k, label, kind) in enumerate(items):
            r, c = divmod(idx, cols)
            ix, iy = x + 10 + c * 170 + 10, y + 44 + r * 90 + 8
            base = f"html=1;whiteSpace=wrap;fontSize=11;strokeColor={color};strokeWidth=1;fillColor=#ffffff;shadow=1;"
            if kind == "d":
                self.vertex(label, base + "shape=cylinder3;boundedLbl=1;backgroundOutline=1;size=10;", ix, iy - 2, 150, 62, key=k)
            elif kind == "x":
                self.vertex(label, base + "rhombus;fontSize=10;", ix, iy - 6, 150, 70, key=k)
            elif kind.startswith("a:"):
                _, cat, icon = kind.split(":")
                self.vertex(label, base + "rounded=1;arcSize=12;spacingLeft=36;", ix, iy, 150, 54, key=k)
                self.vertex("", f"shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.{icon};sketch=0;html=1;"
                            f"fillColor={ICON_FILL[cat]};strokeColor=#ffffff;fontColor=#ffffff;", ix + 6, iy + 13, 28, 28)
            else:
                self.vertex(label, base + "rounded=1;arcSize=12;", ix, iy, 150, 54, key=k)
        self.width_used = max(getattr(self, "width_used", 0), x + w)
        return w, h

    def edge(self, a, b, label="", dashed=False, color="#546E7A"):
        s, t = self.keys[a], self.keys[b]
        i = self.nid()
        style = (f"edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=block;endFill=1;strokeWidth=1.5;strokeColor={color};"
                 + ("dashed=1;" if dashed else ""))
        xml = f'<mxCell id="{i}" style="{style}" edge="1" parent="1" source="{s}" target="{t}"><mxGeometry relative="1" as="geometry"/></mxCell>'
        if label:
            li = self.nid()
            xml += (f'<mxCell id="{li}" value="{q(label)}" style="edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];fontSize=10;labelBackgroundColor=#ffffff;" '
                    f'vertex="1" connectable="0" parent="{i}"><mxGeometry relative="1" as="geometry"><mxPoint as="offset"/></mxGeometry></mxCell>')
        self.edges.append(xml)

    def xml(self, idx):
        body = "".join(self.cells) + "".join(self.edges)
        return (f'<diagram id="page{idx}" name="{q(self.name)}"><mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" '
                f'connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{self.w}" pageHeight="{self.h}" math="0" shadow="0">'
                f'<root><mxCell id="0"/><mxCell id="1" parent="0"/>{body}</root></mxGraphModel></diagram>')


pages = []

# ───────────────────────── 1. Logical architecture ─────────────────────────
p = Page("1 Logical Architecture", "1 · Logical Architecture: Invoice-to-PO Reconciliation", 1700, 900)
p.container("users", "👥 USER & SOURCE LAYER", BLUE, 30, 70, 1, [
    ("drive", "📁 Google Drive folders (invoices, POs)", "c"),
    ("analyst", "🧑‍💼 AP Analyst (exception review)", "c"),
    ("proc", "🧑‍🔧 Procurement / Controller", "c"),
    ("auditor", "🔍 Internal Audit", "c"),
    ("erp", "🏢 Downstream backend / ERP", "c")])
p.container("ingest", "🌐 APPLICATION & API LAYER", TEAL, 250, 70, 1, [
    ("watcher", "🔎 Drive Watcher (changes API)", "a:compute:lambda"),
    ("queue", "📬 Intake Queue + DLQ", "a:app:sqs"),
    ("apigw", "🚪 Existing Backend API", "a:app:api_gateway"),
    ("waf", "🛡️ WAF + Auth (OIDC)", "a:sec:waf")])
p.container("orch", "⚙️ ORCHESTRATION", GREY, 470, 70, 1, [
    ("sfn", "🔀 Step Functions (per-doc workflow)", "a:app:step_functions"),
    ("idem", "🔑 Idempotency guard (doc hash + rule ver)", "d"),
    ("retry", "♻️ Retry / backoff / DLQ redrive", "c"),
    ("exq", "⚠️ Exception router → review queue", "c")])
p.container("ai", "🧠 AI / ML & RULES LAYER", PURPLE, 690, 70, 2, [
    ("cls", "🏷️ Doc classifier (inv/PO/credit)", "c"),
    ("textract", "📄 Textract AnalyzeExpense", "a:ml:textract"),
    ("llm", "🤖 Bedrock multimodal verifier", "a:ml:bedrock"),
    ("pomatch", "🔗 PO identification (deterministic)", "c"),
    ("lines", "📐 Line matcher (embed + Hungarian)", "c"),
    ("rules", "🧮 Rules engine (Decimal, tolerances)", "a:compute:fargate"),
    ("dup", "🔁 Duplicate / repeated-billing", "c"),
    ("risk", "🚨 Risk scorer (IsoForest→LightGBM)", "a:ml:sagemaker")])
p.container("data", "🗄️ DATA LAYER", ORANGE, 1070, 70, 2, [
    ("s3raw", "Raw documents (S3, immutable)", "d"),
    ("s3ev", "Evidence store (S3 Object Lock)", "d"),
    ("aurora", "Results & anomalies (Aurora PG)", "d"),
    ("po", "PO / supplier master cache", "d"),
    ("policy", "Policy & tolerance versions", "d"),
    ("audit", "Decision audit log", "d")])
p.container("sec", "🔐 SECURITY LAYER", RED, 30, 600, 5, [
    ("iam", "🪪 IAM least-privilege roles", "a:sec:identity_and_access_management"),
    ("kms", "🔑 KMS customer keys", "a:sec:key_management_service"),
    ("sm", "🗝️ Secrets Manager (Drive SA)", "a:sec:secrets_manager"),
    ("guard", "🛑 Bedrock Guardrails / schema check", "a:ml:bedrock"),
    ("ct", "📜 CloudTrail", "a:mgmt:cloudtrail")])
p.container("ops", "📈 OPERATIONS & OBSERVABILITY", GREY, 930, 600, 3, [
    ("cw", "📊 CloudWatch / Grafana", "a:mgmt:cloudwatch"),
    ("otel", "🔭 OpenTelemetry traces", "a:mgmt:xray"),
    ("drift", "📉 Drift & review-rate monitor", "c")])
for a, b, l in [("drive", "watcher", "Changes API / poll"), ("watcher", "queue", "File events"), ("queue", "sfn", "Trigger"),
                ("sfn", "idem", "Dedup check"), ("sfn", "cls", "Classify"), ("cls", "textract", "Extract"),
                ("textract", "llm", "Low-confidence fields"), ("llm", "pomatch", "Validated JSON"),
                ("pomatch", "lines", "Candidate PO"), ("lines", "rules", "Line pairs"), ("rules", "dup", "Result"),
                ("dup", "risk", "Signals"), ("rules", "aurora", "Persist outcome"), ("rules", "s3ev", "Evidence bundle"),
                ("sfn", "exq", "Unsafe / ambiguous"), ("exq", "analyst", "Review queue"),
                ("watcher", "s3raw", "Copy original"), ("pomatch", "po", "Lookup"), ("rules", "policy", "Policy vN"),
                ("apigw", "aurora", "Query results"), ("erp", "apigw", "REST (existing contract)"),
                ("auditor", "audit", "Evidence trace")]:
    p.edge(a, b, l)
pages.append(p)

# ───────────────────────── 2. Infrastructure ─────────────────────────
p = Page("2 Infrastructure", "2 · Infrastructure Architecture (AWS, primary region, 2 AZ)", 1700, 960)
G = ("points=[];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;container=1;pointerEvents=0;"
     "collapsible=0;recursiveResize=0;verticalAlign=top;align=left;spacingLeft=30;")
cloud = p.vertex("AWS Cloud", G + "shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_aws_cloud_alt;strokeColor=#232F3E;fillColor=none;fontColor=#232F3E;", 20, 70, 1640, 860)
region = p.vertex("Region (primary; DR region in Resilience view)", G + "shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_region;strokeColor=#147EBA;fillColor=none;fontColor=#147EBA;dashed=1;", 20, 40, 1600, 800, cloud)


def icon(page, label, cat, res, x, y, parent, key=None):
    page.vertex(label, f"sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor={ICON_FILL[cat]};strokeColor=#ffffff;"
                f"dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;whiteSpace=nowrap;"
                f"aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.{res};", x, y, 48, 48, parent, key)


icon(p, "Route 53", "net", "route_53", 30, 70, region, "r53")
icon(p, "WAF", "sec", "waf", 30, 190, region, "waf")
icon(p, "API Gateway", "app", "api_gateway", 30, 310, region, "apigw")
icon(p, "Cognito", "sec", "cognito", 30, 430, region, "cog")
vpc = p.vertex("VPC 10.20.0.0/16", G + "shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc2;strokeColor=#8C4FFF;fillColor=none;fontColor=#8C4FFF;", 160, 40, 960, 730, region)
icon(p, "Internet GW", "net", "internet_gateway", 30, 50, vpc, "igw")
icon(p, "Internal ALB", "net", "application_load_balancer", 160, 50, vpc, "alb")
icon(p, "S3 Gateway EP", "net", "endpoints", 300, 50, vpc, "epS3")
icon(p, "Interface EP (Textract/Bedrock)", "net", "endpoints", 430, 50, vpc, "epAI")
AZ = G + "strokeColor=#147EBA;fillColor=none;dashed=1;fontColor=#147EBA;shape=rect;"
for az, ax in (("a", 20), ("b", 490)):
    azid = p.vertex(f"Availability Zone {az}", AZ, ax, 150, 450, 560, vpc)
    pub = p.vertex("Public subnet", G + "shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;grStroke=0;strokeColor=#7AA116;fillColor=#E9F3E6;fontColor=#248814;", 10, 35, 430, 110, azid)
    icon(p, "NAT Gateway", "net", "nat_gateway", 30, 25, pub, f"nat{az}")
    app = p.vertex("Private app subnet", G + "shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;grStroke=0;strokeColor=#D6B656;fillColor=#FFF2CC;fontColor=#7D6A00;", 10, 160, 430, 170, azid)
    icon(p, "Fargate: API", "compute", "fargate", 40, 40, app, f"fapi{az}")
    icon(p, "Fargate: Reconciler", "compute", "fargate", 190, 40, app, f"frec{az}")
    icon(p, "Lambda: Watcher", "compute", "lambda", 340, 40, app, f"lam{az}")
    db = p.vertex("Private data subnet", G + "shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;grStroke=0;strokeColor=#B85450;fillColor=#FFCCCC;fontColor=#990000;", 10, 345, 430, 190, azid)
    icon(p, "Aurora PG (writer)" if az == "a" else "Aurora PG (reader)", "db", "aurora", 70, 45, db, f"aur{az}")
    icon(p, "ElastiCache (cache)", "db", "elasticache", 270, 45, db, f"cache{az}")
svc = [("S3 raw", "storage", "s3"), ("S3 evidence", "storage", "s3"), ("SQS + DLQ", "app", "sqs"), ("Step Functions", "app", "step_functions"),
       ("Textract", "ml", "textract"), ("Bedrock", "ml", "bedrock"), ("SageMaker EP", "ml", "sagemaker"), ("KMS", "sec", "key_management_service"),
       ("CloudWatch", "mgmt", "cloudwatch"), ("Secrets Mgr", "sec", "secrets_manager"), ("EventBridge", "app", "eventbridge_default_bus"), ("DynamoDB", "db", "dynamodb")]
p.vertex("Regional managed services (outside VPC)", "text;html=1;fontStyle=1;fontSize=13;strokeColor=none;fillColor=none;", 1140, 40, 440, 24, region)
for n, (lbl, cat, res) in enumerate(svc):
    icon(p, lbl, cat, res, 1160 + (n % 3) * 140, 90 + (n // 3) * 150, region, f"svc{n}")
for a, b, l in [("apigw", "alb", "HTTPS via VPC Link"), ("alb", "fapia", "HTTP"), ("frecb", "aurb", "SQL / TLS"), ("freca", "aura", "SQL / TLS"),
                ("freca", "epS3", "S3 (private)"), ("frecb", "epAI", "Textract / Bedrock"), ("nata", "igw", "Egress (Drive API)"),
                ("lama", "nata", "Drive API"), ("r53", "waf", "DNS"), ("waf", "apigw", "Filtered")]:
    p.edge(a, b, l)
pages.append(p)

# ───────────────────────── 3. Security ─────────────────────────
p = Page("3 Security", "3 · Security Architecture & Governance", 1500, 1000)
p.container("iam", "🪪 IDENTITY & ACCESS (TL)", BLUE, 30, 70, 3, [
    ("cog", "Cognito / OIDC SSO", "a:sec:cognito"), ("role", "Per-service IAM roles", "a:sec:identity_and_access_management"),
    ("sso", "IAM Identity Center (staff)", "a:sec:single_sign_on"), ("sa", "Drive service account (read-only folders)", "c"),
    ("rbac", "RBAC: AP / Procurement / Audit", "c"), ("sm", "Secrets Manager rotation", "a:sec:secrets_manager")])
p.container("pol", "🛑 POLICY & AI GUARDRAILS (TR)", PURPLE, 560, 70, 3, [
    ("waf", "WAF managed rules + rate limit", "a:sec:waf"), ("gr", "Bedrock Guardrails", "a:ml:bedrock"),
    ("inj", "Prompt-injection defense: document text = data", "c"), ("schema", "Strict JSON schema validation", "c"),
    ("pii", "PII / bank-data redaction in logs", "c"), ("scp", "SCPs / permission boundaries", "c")])
p.container("aud", "📜 AUDIT & EVIDENCE (BL)", GREEN, 30, 400, 3, [
    ("ct", "CloudTrail (mgmt + data events)", "a:mgmt:cloudtrail"), ("lock", "S3 Object Lock evidence", "d"),
    ("cfg", "AWS Config rules", "a:mgmt:config"), ("sh", "Security Hub", "a:sec:security_hub"),
    ("aa", "IAM Access Analyzer", "a:sec:identity_and_access_management"), ("alog", "Immutable decision log", "d")])
p.container("thr", "🚨 THREAT DETECTION & NETWORK (BR)", RED, 560, 400, 3, [
    ("gd", "GuardDuty", "a:sec:guardduty"), ("insp", "Inspector (images, Lambda)", "a:sec:inspector"),
    ("fl", "VPC Flow Logs", "a:net:virtual_private_cloud"), ("nfw", "Private subnets + SGs/NACLs", "c"),
    ("ecr", "ECR image scanning + signing", "a:compute:elastic_container_registry"), ("shield", "Shield Standard", "a:sec:shield")])
p.container("enc", "🔒 DATA PROTECTION BAR", AMBER, 30, 730, 6, [
    ("kms", "KMS CMKs per data class", "a:sec:key_management_service"), ("tls", "TLS 1.2+/1.3 in transit", "c"),
    ("rest", "Encryption at rest (S3/Aurora/SQS)", "c"), ("ret", "Retention & legal-hold policy", "c"),
    ("mfa", "MFA for privileged roles", "c"), ("dlp", "Macie scan on raw bucket", "a:sec:macie")])
p.text("Legend: red = threat; green = audit; purple = AI policy; blue = identity. Anomaly ≠ fraud verdict: advisory only.", 30, 940, 1000, 24, "fontSize=11;fontStyle=2;")
for a, b, l in [("cog", "role", "Token → role"), ("sa", "sm", "Credential"), ("waf", "gr", "Filtered input"), ("gr", "schema", "Model output"),
                ("ct", "lock", "Log archive"), ("gd", "sh", "Findings"), ("role", "kms", "Key policy"), ("rbac", "cog", "Groups")]:
    p.edge(a, b, l)
pages.append(p)

# ───────────────────────── 4. Observability ─────────────────────────
p = Page("4 Observability", "4 · Observability, Logging & Monitoring", 1500, 1000)
rows = [
    ("COLLECTION", BLUE, 70, [("otel", "OTel / ADOT collector", "c"), ("logs", "CloudWatch Logs (structured JSON)", "a:mgmt:cloudwatch"),
                              ("xray", "X-Ray traces", "a:mgmt:xray"), ("amp", "Amazon Managed Prometheus", "c"),
                              ("flow", "VPC Flow Logs", "c"), ("evt", "Domain events (EventBridge)", "a:app:eventbridge_default_bus")]),
    ("VISUALIZATION", TEAL, 270, [("graf", "Grafana dashboards", "c"), ("cwd", "CloudWatch dashboards", "a:mgmt:cloudwatch"),
                                  ("athena", "Athena audit queries", "a:db:athena"), ("qs", "QuickSight KPIs (STP, leakage)", "a:db:quicksight"),
                                  ("evid", "Evidently drift reports", "c")]),
    ("ALERTING", RED, 470, [("alarm", "CloudWatch alarms", "a:mgmt:cloudwatch"), ("sns", "SNS → on-call", "a:app:sns"),
                            ("slo", "SLO burn-rate alerts", "c"), ("bud", "Budgets & anomaly alerts", "c"),
                            ("ovr", "Reviewer-override-rate alert", "c")]),
    ("OPERATIONS", GREEN, 670, [("rb", "Runbooks (SSM)", "a:mgmt:systems_manager"), ("redrive", "DLQ redrive tool", "c"),
                                ("rep", "Safe reprocess API", "c"), ("exq", "Exception queue age", "c"),
                                ("post", "Post-incident review", "c")]),
]
for key, (t, col, y, items) in enumerate(rows):
    p.container(f"row{key}", f"{t}", col, 30, y, 6, items)
p.text("Tracked: queue age · p95 latency/doc · extraction confidence · LLM-fallback rate · review rate · STP % · unsafe-approval count (must be 0) · token/page cost", 30, 900, 1400, 40, "fontSize=12;fontStyle=2;")
for a, b, l in [("otel", "graf", "Metrics"), ("logs", "athena", "Query"), ("xray", "cwd", "Traces"), ("graf", "alarm", "Thresholds"),
                ("alarm", "sns", "Notify"), ("sns", "rb", "Page → runbook"), ("evid", "ovr", "Drift signal"), ("exq", "slo", "Age metric")]:
    p.edge(a, b, l)
pages.append(p)

# ───────────────────────── 5. MLOps CI/CD ─────────────────────────
p = Page("5 CI-CD & MLOps", "5 · CI/CD & MLOps Pipeline", 1700, 800)
p.container("src", "SOURCE", BLUE, 30, 70, 1, [("git", "GitHub repo (trunk + PRs)", "c"), ("pr", "PR checks / CODEOWNERS", "c"), ("gold", "Golden set (S3 + DVC)", "d")])
p.container("ci", "CI", TEAL, 240, 70, 1, [("lint", "Lint + type check", "c"), ("ut", "Unit + property tests", "c"), ("reg", "Golden-set regression GATE", "x"), ("scan", "Trivy / Inspector scan", "c")])
p.container("train", "TRAIN / TUNE", PURPLE, 450, 70, 1, [("label", "Reviewer labels (Ground Truth)", "c"), ("ft", "LayoutLMv3 fine-tune (SageMaker)", "a:ml:sagemaker"), ("opt", "Optuna thresholds", "c"), ("mlf", "MLflow tracking", "c")])
p.container("regs", "REGISTRY", ORANGE, 660, 70, 1, [("mreg", "Model registry (Exp→Stg→Cand→Prod)", "d"), ("ecr", "ECR images (signed)", "a:compute:elastic_container_registry"), ("pver", "Prompt / schema / policy versions", "d")])
p.container("dep", "DEPLOY", GREEN, 870, 70, 1, [("tf", "Terraform plan/apply", "c"), ("shadow", "Shadow mode", "c"), ("canary", "Canary by supplier segment", "c"), ("prod", "Production", "a:compute:fargate")])
p.container("mon", "MONITOR", GREY, 1080, 70, 1, [("drift", "Drift (PSI/KS)", "c"), ("rev", "Review & override rate", "c"), ("cost", "Cost / page", "c")])
for a, b, l in [("git", "lint", "Push"), ("pr", "ut", "Trigger"), ("gold", "reg", "Eval set"), ("reg", "scan", "Pass"), ("scan", "ecr", "Build & push"),
                ("label", "ft", "Training data"), ("ft", "mlf", "Metrics"), ("mlf", "mreg", "Register"), ("mreg", "tf", "Promote"),
                ("ecr", "tf", "Image"), ("pver", "shadow", "Config"), ("shadow", "canary", "No unsafe diffs"), ("canary", "prod", "Approved"),
                ("prod", "drift", "Telemetry")]:
    p.edge(a, b, l)
p.edge("rev", "label", "Retrain loop (corrections → labels)", dashed=True, color="#C62828")
pages.append(p)

# ───────────────────────── 6. Data lineage & privacy ─────────────────────────
p = Page("6 Data Lineage & Privacy", "6 · Data Lineage & Privacy Governance", 1700, 950)
p.container("l1", "① INGEST", BLUE, 30, 70, 3, [("src", "Google Drive file (id, version)", "c"), ("hash", "SHA-256 content hash", "c"), ("raw", "Raw S3 (versioned, immutable)", "d")])
p.container("l2", "② DETECT & PROTECT", RED, 600, 70, 3, [("macie", "Macie / PII scan", "a:sec:macie"), ("mask", "Mask bank/PII in logs & prompts", "c"), ("tok", "Tokenise bank details", "c")])
p.container("l3", "③ EXTRACT & DERIVE", PURPLE, 30, 300, 3, [("ext", "Extracted fields (+confidence, bbox)", "d"), ("run", "Extraction run id + model/prompt ver", "d"), ("cmp", "Comparison results & variances", "d")])
p.container("l4", "④ DECIDE & RECORD", ORANGE, 600, 300, 3, [("pol", "Policy / rule version", "d"), ("out", "Outcome + anomaly codes", "d"), ("ev", "Evidence bundle (Object Lock)", "d")])
p.container("l5", "⑤ GOVERN", GREEN, 30, 530, 4, [("cat", "Glue Data Catalog / lineage graph", "a:db:glue"), ("ol", "OpenLineage events", "c"), ("rls", "Row-level security per legal entity", "c"), ("ck", "Per-entity KMS keys", "a:sec:key_management_service")])
p.container("l6", "⑥ RETAIN & ACCESS", GREY, 30, 760, 5, [("ret", "Retention + lifecycle tiers", "c"), ("hold", "Legal hold", "c"), ("acc", "Access logs (CloudTrail data events)", "a:mgmt:cloudtrail"), ("dsr", "Redaction / deletion workflow", "c"), ("api", "API: authorized consumers only", "c")])
p.text("Lineage key: doc hash → extraction run → policy version → outcome → evidence bundle. Any decision is reproducible.", 30, 900, 1500, 24, "fontSize=12;fontStyle=2;")
for a, b, l in [("src", "hash", "Fingerprint"), ("hash", "raw", "Store"), ("raw", "macie", "Scan"), ("macie", "mask", "Findings"), ("mask", "tok", "Redact"),
                ("raw", "ext", "Extract"), ("ext", "run", "Version"), ("run", "cmp", "Reconcile"), ("cmp", "out", "Rules"), ("pol", "out", "Policy"),
                ("out", "ev", "Bundle"), ("ev", "cat", "Register"), ("cat", "ol", "Emit"), ("out", "rls", "Isolate"), ("ev", "ret", "Lifecycle")]:
    p.edge(a, b, l)
pages.append(p)

# ───────────────────────── 7. Resilience ─────────────────────────
p = Page("7 Resilience & Fallback", "7 · Resilience, HA & Multi-Provider Fallback", 1700, 950)
p.container("prim", "PRIMARY REGION (active)", BLUE, 30, 70, 2, [("apiP", "API / Fargate (2 AZ)", "a:compute:fargate"), ("sfnP", "Step Functions", "a:app:step_functions"), ("auP", "Aurora writer", "d"), ("s3P", "S3 raw + evidence", "d"), ("sqsP", "SQS + DLQ", "a:app:sqs"), ("cbr", "Circuit breaker + backoff", "c")])
p.container("dr", "DR REGION (warm standby)", GREEN, 30, 420, 2, [("apiD", "API (scaled to min)", "a:compute:fargate"), ("auD", "Aurora Global replica", "d"), ("s3D", "S3 CRR replica", "d"), ("tfD", "Terraform-ready stack", "c")])
p.container("fb", "EXTRACTION FALLBACK CHAIN", PURPLE, 450, 70, 2, [("t1", "1 · Textract AnalyzeExpense", "a:ml:textract"), ("t2", "2 · Bedrock multimodal (model A)", "a:ml:bedrock"), ("t3", "3 · Bedrock alt. model / region", "a:ml:bedrock"),
                                                                    ("t4", "4 · Self-hosted LayoutLMv3 (SageMaker)", "a:ml:sagemaker"), ("t5", "5 · Manual review queue (never guess)", "c"), ("conf", "Confidence gate per field", "x")])
p.container("rec", "RECOVERY PATTERNS", ORANGE, 450, 420, 2, [("r53", "Route 53 health failover", "a:net:route_53"), ("bk", "AWS Backup + PITR", "a:storage:backup"), ("dlq", "DLQ + redrive", "c"), ("idem", "Idempotent replay", "c"), ("chaos", "Game days / chaos tests", "c"), ("rto", "RTO 4h · RPO 15m (to be agreed)", "c")])
for a, b, l in [("apiP", "sfnP", "Start"), ("sfnP", "t1", "Primary"), ("t1", "conf", "Fields"), ("conf", "t2", "Low conf"), ("t2", "t3", "Throttle/err"), ("t3", "t4", "Outage"),
                ("t4", "t5", "Still unsure"), ("sqsP", "dlq", "Max retries"), ("auP", "auD", "Replication"), ("s3P", "s3D", "CRR"), ("cbr", "t2", "Open → skip")]:
    p.edge(a, b, l)
pages.append(p)

# ───────────────────────── 8. Orchestration ─────────────────────────
p = Page("8 Workflow Orchestration", "8 · Workflow Orchestration & Bounded AI Workers (no autonomous agents)", 1700, 950)
p.container("sup", "SUPERVISOR (deterministic state machine)", GREY, 30, 70, 2, [("sm", "Step Functions: per-document workflow", "a:app:step_functions"), ("st", "State store (DynamoDB)", "d"), ("ctx", "Run context: policy/model versions", "c"), ("hum", "Human review task token", "c")])
p.container("wk", "WORKERS (each single-purpose)", PURPLE, 400, 70, 3, [("w1", "Classifier", "c"), ("w2", "Extractor (Textract)", "c"), ("w3", "Verifier (LLM, schema-bound)", "c"), ("w4", "Validator (math, dates, IDs)", "c"),
                                                                     ("w5", "PO resolver", "c"), ("w6", "Line matcher", "c"), ("w7", "Reconciler (rules)", "c"), ("w8", "Anomaly checker", "c"), ("w9", "Evidence writer", "c")])
p.container("tools", "TOOL REGISTRY (allow-listed, read-only unless noted)", BLUE, 400, 380, 3, [("tdrive", "Drive API (read)", "c"), ("terp", "PO / ERP API (read)", "c"), ("tsup", "Supplier master (read)", "c"), ("tres", "Results API (write, existing contract)", "c"), ("tdb", "Aurora (write results)", "d"), ("tevid", "S3 evidence (write-once)", "d")])
p.container("gates", "DECISION GATES", RED, 30, 330, 2, [("g1", "Fields confident & valid?", "x"), ("g2", "Exactly one eligible PO?", "x"), ("g3", "All mandatory checks pass?", "x"), ("g4", "Duplicate suspected?", "x")])
p.container("out", "OUTCOMES (BRD §10)", GREEN, 1000, 70, 2, [("o1", "Matched / within tolerance", "c"), ("o2", "Partially matched", "c"), ("o3", "Discrepancy detected", "c"), ("o4", "Duplicate suspected", "c"), ("o5", "Extraction failed / Requires review", "c"), ("o6", "Processing failed (retry)", "c")])
p.text("Sandbox: the LLM has NO tool access, cannot choose a PO and cannot approve. It returns schema-bound JSON that rules verify.", 30, 700, 1500, 24, "fontSize=12;fontStyle=2;")
for a, b, l in [("sm", "w1", "Invoke"), ("w1", "w2", ""), ("w2", "w3", "Low conf only"), ("w3", "w4", ""), ("w4", "g1", ""), ("g1", "w5", "Yes"), ("w5", "g2", ""),
                ("g2", "w6", "Yes"), ("w6", "w7", ""), ("w7", "w8", ""), ("w8", "g3", ""), ("g3", "o1", "Yes"), ("g3", "g4", "Check"), ("g4", "o4", "Yes"),
                ("g1", "o5", "No"), ("g2", "hum", "Ambiguous"), ("w9", "tevid", "Write once"), ("w5", "terp", "Read"), ("w9", "tdb", "Persist"), ("sm", "st", "State")]:
    p.edge(a, b, l)
pages.append(p)

# ───────────────────────── 9. FinOps ─────────────────────────
p = Page("9 FinOps", "9 · FinOps & Cost Optimization (LLM/Doc-AI spend control)", 1600, 900)
p.container("tier", "TIERED EXTRACTION ROUTING", PURPLE, 30, 70, 2, [("h", "Doc-hash cache (skip re-extraction)", "d"), ("tx", "Textract first (cheapest per page)", "a:ml:textract"), ("sm", "Small LLM for low-conf fields", "a:ml:bedrock"), ("lg", "Larger LLM only for hard layouts", "a:ml:bedrock"),
                                                              ("pc", "Prompt caching for schema/instructions", "c"), ("btch", "Batch inference for backlog", "c")])
p.container("cache", "CACHING", TEAL, 400, 70, 2, [("emb", "Embedding cache (line descriptions)", "a:db:elasticache"), ("sup", "Supplier / PO lookup cache", "d"), ("ttl", "TTL + invalidation on PO change", "c"), ("hr", "Cache hit-rate metric", "c")])
p.container("quota", "QUOTAS & BUDGETS", RED, 770, 70, 2, [("bud", "AWS Budgets per env", "c"), ("ent", "Per-entity page/token quotas", "c"), ("anom", "Cost Anomaly Detection", "c"), ("cap", "Hard LLM spend cap → fallback to review", "x")])
p.container("infra", "INFRA SAVINGS", GREEN, 30, 400, 2, [("spot", "Fargate Spot for batch workers", "a:compute:fargate"), ("life", "S3 lifecycle (IA/Glacier)", "a:storage:s3"), ("ep", "VPC endpoints vs NAT data cost", "c"), ("rs", "Aurora Serverless v2 scaling", "a:db:aurora")])
p.container("vis", "COST VISIBILITY", BLUE, 400, 400, 2, [("tag", "Cost-allocation tags (entity, stage)", "c"), ("cur", "CUR → Athena", "a:db:athena"), ("kpi", "Cost per invoice KPI", "c"), ("rev", "Monthly FinOps review", "c")])
for a, b, l in [("h", "tx", "Miss"), ("tx", "sm", "Low conf"), ("sm", "lg", "Still low"), ("emb", "kpi", "Savings"), ("cap", "tx", "Breached"), ("tag", "cur", "Allocate"), ("cur", "kpi", "Report"), ("ent", "cap", "Limit")]:
    p.edge(a, b, l)
pages.append(p)

# ───────────────────────── 10. Governance & HITL ─────────────────────────
p = Page("10 Governance & HITL", "10 · AI Model Governance, Safety & HITL Evaluation", 1700, 950)
p.container("ev", "CONTINUOUS EVALUATION", PURPLE, 30, 70, 1, [("gs", "Golden-set run", "d"), ("m1", "Field F1 / calibration", "c"), ("m2", "PO-ID accuracy", "c"), ("m3", "Unsafe approvals = 0", "c")])
p.container("gt", "GATES", RED, 240, 70, 1, [("d1", "Accuracy ≥ target?", "x"), ("d2", "Zero unsafe approvals?", "x"), ("d3", "Finance sign-off?", "x")])
p.container("st", "REGISTRY STAGES", ORANGE, 450, 70, 2, [("sx", "Experimental", "c"), ("ss", "Staging (shadow)", "c"), ("sc", "Candidate (canary)", "c"), ("sp", "Production", "c")])
p.container("hq", "HUMAN-IN-THE-LOOP", GREEN, 30, 420, 2, [("q", "Exception queue (SLA tracked)", "c"), ("rv", "Reviewer: approve/reject/correct", "c"), ("reason", "Reason codes captured", "c"), ("fb", "Feedback → golden set", "d")])
p.container("po", "POLICY GOVERNANCE", BLUE, 450, 420, 2, [("tolp", "Tolerance & rounding policy", "d"), ("appr", "Controller approval + version", "c"), ("reproc", "Authorised reprocess on rule change", "c"), ("pack", "Audit pack export", "c")])
p.container("sf", "SAFETY CONTROLS", GREY, 870, 70, 2, [("kill", "Kill-switch → review-only mode", "c"), ("pii", "PII / injection tests in CI", "c"), ("card", "Model card + risk register", "c"), ("eu", "EU AI Act / ISO 42001 mapping", "c")])
for a, b, l in [("gs", "m1", "Score"), ("m1", "d1", "Pass?"), ("m3", "d2", ""), ("d1", "sx", "Yes"), ("d2", "ss", "Yes"), ("d3", "sc", "Yes"), ("sc", "sp", "Promote"),
                ("q", "rv", "Assign"), ("rv", "reason", ""), ("reason", "fb", "Label"), ("fb", "gs", "Grow set", ), ("appr", "reproc", "New version"), ("tolp", "appr", "Draft")]:
    p.edge(a, b, l, dashed=(l == "Grow set"))
pages.append(p)

xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<mxfile host="app.diagrams.net" agent="generate_drawio.py" version="24.0.0">'
       + "".join(pg.xml(i + 1) for i, pg in enumerate(pages)) + "</mxfile>\n")
with open(OUT, "w", encoding="utf-8") as f:
    f.write(xml)
print("wrote", OUT, len(pages), "pages")
