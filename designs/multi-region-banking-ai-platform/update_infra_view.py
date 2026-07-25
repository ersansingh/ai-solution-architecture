"""
Replaces Page 2 (Infrastructure View) in multi_region_banking_ai.drawio
with a fully detailed AWS/Azure native icon diagram.
"""

import re

DRAWIO_PATH = r"c:\Users\DELL\Documents\GitHub\ai-solution-architecture\designs\multi-region-banking-ai-platform\multi_region_banking_ai.drawio"

NEW_PAGE2 = '''  <!-- Page 2: Multi-Region Sovereign Infrastructure View — AWS/Azure Native Icons -->
  <diagram id="view-2-infra" name="2. Multi-Region Sovereign Infrastructure View">
    <mxGraphModel dx="2400" dy="1300" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="2400" pageHeight="1300" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <!-- ================================================================ -->
        <!-- REGION 1: AWS us-east-1  North America Sovereign Hub (VPC)      -->
        <!-- ================================================================ -->
        <mxCell id="na-vpc" value="AWS VPC &amp;mdash; us-east-1  (10.0.0.0/16)&amp;#xa;North America Sovereign Hub | Fed / OCC / SEC Compliant" style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc;strokeColor=#8C4FFF;fillColor=#F4F0FD;fontStyle=1;fontSize=11;fontColor=#232F3E;whiteSpace=wrap;html=1;verticalAlign=top;align=center;spacingTop=5;" vertex="1" parent="1">
          <mxGeometry x="30" y="30" width="720" height="1220" as="geometry" />
        </mxCell>

        <!-- Internet Gateway NA -->
        <mxCell id="na-igw" value="Internet Gateway" style="shape=mxgraph.aws4.internet_gateway;fillColor=#8C4FFF;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="na-vpc">
          <mxGeometry x="100" y="40" width="60" height="60" as="geometry" />
        </mxCell>
        <mxCell id="na-igw-lbl" value="igw-na-prod" style="text;html=1;strokeColor=none;fillColor=none;align=center;fontSize=9;" vertex="1" parent="na-vpc">
          <mxGeometry x="75" y="103" width="110" height="16" as="geometry" />
        </mxCell>

        <!-- AWS Direct Connect NA -->
        <mxCell id="na-dx" value="AWS Direct Connect&amp;#xa;10 Gbps Dedicated" style="shape=mxgraph.aws4.direct_connect;fillColor=#8C4FFF;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="na-vpc">
          <mxGeometry x="310" y="40" width="60" height="60" as="geometry" />
        </mxCell>
        <mxCell id="na-dx-lbl" value="dx-na-10g-primary" style="text;html=1;strokeColor=none;fillColor=none;align=center;fontSize=9;" vertex="1" parent="na-vpc">
          <mxGeometry x="275" y="103" width="130" height="16" as="geometry" />
        </mxCell>

        <!-- AWS Transit Gateway NA -->
        <mxCell id="na-tgw" value="Transit Gateway&amp;#xa;(10.0.0.0/8 RT)" style="shape=mxgraph.aws4.transit_gateway;fillColor=#8C4FFF;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="na-vpc">
          <mxGeometry x="530" y="40" width="60" height="60" as="geometry" />
        </mxCell>
        <mxCell id="na-tgw-lbl" value="tgw-na-global-backbone" style="text;html=1;strokeColor=none;fillColor=none;align=center;fontSize=9;" vertex="1" parent="na-vpc">
          <mxGeometry x="490" y="103" width="140" height="16" as="geometry" />
        </mxCell>

        <!-- NA Public Subnet -->
        <mxCell id="na-pub-sub" value="Public Subnet &amp;mdash; 10.0.1.0/24  (AZ: us-east-1a)" style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_subnet;strokeColor=#147EBA;fillColor=#E6F2F8;fontStyle=1;fontSize=10;verticalAlign=top;spacingTop=4;whiteSpace=wrap;html=1;" vertex="1" parent="na-vpc">
          <mxGeometry x="30" y="140" width="660" height="170" as="geometry" />
        </mxCell>
        <mxCell id="na-alb" value="App Load Balancer" style="shape=mxgraph.aws4.application_load_balancer;fillColor=#147EBA;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="na-pub-sub">
          <mxGeometry x="30" y="60" width="60" height="60" as="geometry" />
        </mxCell>
        <mxCell id="na-alb-lbl" value="alb-na-prod" style="text;html=1;strokeColor=none;fillColor=none;align=center;fontSize=9;" vertex="1" parent="na-pub-sub">
          <mxGeometry x="10" y="123" width="100" height="16" as="geometry" />
        </mxCell>
        <mxCell id="na-waf" value="AWS WAF v2" style="shape=mxgraph.aws4.shield;fillColor=#DD344C;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="na-pub-sub">
          <mxGeometry x="200" y="60" width="60" height="60" as="geometry" />
        </mxCell>
        <mxCell id="na-nat" value="NAT Gateway" style="shape=mxgraph.aws4.nat_gateway;fillColor=#147EBA;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="na-pub-sub">
          <mxGeometry x="390" y="60" width="60" height="60" as="geometry" />
        </mxCell>
        <mxCell id="na-nat-lbl" value="nat-gw-na (EIP: 3.xx.xx.xx)" style="text;html=1;strokeColor=none;fillColor=none;align=center;fontSize=9;" vertex="1" parent="na-pub-sub">
          <mxGeometry x="360" y="123" width="130" height="16" as="geometry" />
        </mxCell>
        <mxCell id="na-r53" value="Route 53&amp;#xa;Health Check" style="shape=mxgraph.aws4.route_53;fillColor=#8C4FFF;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="na-pub-sub">
          <mxGeometry x="555" y="60" width="60" height="60" as="geometry" />
        </mxCell>

        <!-- NA Private App Subnet -->
        <mxCell id="na-app-sub" value="Private App Subnet &amp;mdash; 10.0.2.0/24  (AZ: us-east-1a / 1b)" style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_subnet;strokeColor=#147EBA;fillColor=#DCE9F2;fontStyle=1;fontSize=10;verticalAlign=top;spacingTop=4;whiteSpace=wrap;html=1;" vertex="1" parent="na-vpc">
          <mxGeometry x="30" y="340" width="660" height="310" as="geometry" />
        </mxCell>
        <mxCell id="na-eks" value="Amazon EKS Cluster&amp;#xa;LangGraph + LiteLLM&amp;#xa;+ Envoy Gateway" style="shape=mxgraph.aws4.eks;fillColor=#F58534;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="na-app-sub">
          <mxGeometry x="30" y="55" width="65" height="65" as="geometry" />
        </mxCell>
        <mxCell id="na-eks-lbl" value="eks-na-prod&amp;#xa;3 AZs, m5.4xlarge" style="text;html=1;strokeColor=none;fillColor=none;align=center;fontSize=9;" vertex="1" parent="na-app-sub">
          <mxGeometry x="5" y="123" width="115" height="28" as="geometry" />
        </mxCell>
        <mxCell id="na-gpu" value="GPU Node Group&amp;#xa;4x NVIDIA A10G&amp;#xa;vLLM Llama-3.1-70B" style="shape=mxgraph.aws4.ec2;fillColor=#F58534;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="na-app-sub">
          <mxGeometry x="200" y="55" width="65" height="65" as="geometry" />
        </mxCell>
        <mxCell id="na-apigw" value="API Gateway&amp;#xa;REST + WebSocket" style="shape=mxgraph.aws4.api_gateway;fillColor=#E7157B;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="na-app-sub">
          <mxGeometry x="390" y="55" width="65" height="65" as="geometry" />
        </mxCell>
        <mxCell id="na-bedrock" value="AWS Bedrock&amp;#xa;Claude / Titan&amp;#xa;Zero-Retention" style="shape=mxgraph.aws4.sagemaker;fillColor=#01A88D;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="na-app-sub">
          <mxGeometry x="560" y="55" width="65" height="65" as="geometry" />
        </mxCell>
        <mxCell id="na-redis" value="ElastiCache Redis&amp;#xa;Semantic Cache" style="shape=mxgraph.aws4.elasticache;fillColor=#C7131F;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="na-app-sub">
          <mxGeometry x="30" y="195" width="65" height="65" as="geometry" />
        </mxCell>
        <mxCell id="na-sm" value="SageMaker&amp;#xa;Embedding Svc" style="shape=mxgraph.aws4.sagemaker;fillColor=#01A88D;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="na-app-sub">
          <mxGeometry x="200" y="195" width="65" height="65" as="geometry" />
        </mxCell>

        <!-- NA Private Data Subnet -->
        <mxCell id="na-data-sub" value="Private Data Subnet &amp;mdash; 10.0.3.0/24  (AZ: us-east-1a / 1b / 1c)" style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_subnet;strokeColor=#147EBA;fillColor=#D0E3EF;fontStyle=1;fontSize=10;verticalAlign=top;spacingTop=4;whiteSpace=wrap;html=1;" vertex="1" parent="na-vpc">
          <mxGeometry x="30" y="680" width="660" height="240" as="geometry" />
        </mxCell>
        <mxCell id="na-opensearch" value="Amazon OpenSearch&amp;#xa;HNSW Vector + BM25" style="shape=mxgraph.aws4.opensearch_service;fillColor=#8C4FFF;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="na-data-sub">
          <mxGeometry x="30" y="70" width="65" height="65" as="geometry" />
        </mxCell>
        <mxCell id="na-rds" value="RDS PostgreSQL&amp;#xa;Multi-AZ CMK" style="shape=mxgraph.aws4.rds;fillColor=#C7131F;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="na-data-sub">
          <mxGeometry x="200" y="70" width="65" height="65" as="geometry" />
        </mxCell>
        <mxCell id="na-s3" value="S3 Sovereign&amp;#xa;KMS CMK AES-256" style="shape=mxgraph.aws4.s3;fillColor=#3F8624;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="na-data-sub">
          <mxGeometry x="390" y="70" width="65" height="65" as="geometry" />
        </mxCell>
        <mxCell id="na-kms" value="AWS KMS&amp;#xa;Customer Managed Key" style="shape=mxgraph.aws4.key_management_service;fillColor=#DD344C;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="na-data-sub">
          <mxGeometry x="560" y="70" width="65" height="65" as="geometry" />
        </mxCell>

        <!-- NA On-Premises -->
        <mxCell id="na-onprem" value="On-Premises DC&amp;#xa;MPLS / SD-WAN BGP" style="shape=mxgraph.aws4.traditional_server;fillColor=#687078;strokeColor=#ffffff;fontColor=#ffffff;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="na-vpc">
          <mxGeometry x="30" y="980" width="65" height="65" as="geometry" />
        </mxCell>
        <mxCell id="na-onprem-lbl" value="corp-dc-na (via Direct Connect)" style="text;html=1;strokeColor=none;fillColor=none;align=center;fontSize=9;" vertex="1" parent="na-vpc">
          <mxGeometry x="0" y="1048" width="130" height="16" as="geometry" />
        </mxCell>
        <mxCell id="na-cw" value="CloudWatch + VPC Flow Logs&amp;#xa;(Security Audit &amp;amp; Observability)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#232F3E;strokeColor=#FF9900;fontColor=#FF9900;fontStyle=1;fontSize=9;" vertex="1" parent="na-vpc">
          <mxGeometry x="390" y="980" width="280" height="50" as="geometry" />
        </mxCell>

        <!-- ================================================================ -->
        <!-- REGION 2: Azure West Europe  EU Sovereign Hub (VNet)            -->
        <!-- ================================================================ -->
        <mxCell id="eu-vnet" value="Azure VNet &amp;mdash; West Europe  (172.16.0.0/16)&amp;#xa;EU Sovereign Hub | GDPR / EU AI Act Stack" style="shape=mxgraph.azure.virtual_network;strokeColor=#0078D4;fillColor=#EBF5FD;fontStyle=1;fontSize=11;fontColor=#032D60;whiteSpace=wrap;html=1;verticalAlign=top;align=center;spacingTop=5;" vertex="1" parent="1">
          <mxGeometry x="810" y="30" width="720" height="1220" as="geometry" />
        </mxCell>

        <!-- Azure ExpressRoute -->
        <mxCell id="eu-er" value="Azure ExpressRoute&amp;#xa;10 Gbps Private Circuit" style="shape=mxgraph.azure.expressroute;fillColor=#0078D4;strokeColor=#ffffff;fontColor=#032D60;fontStyle=1;labelBackgroundColor=none;" vertex="1" parent="eu-vnet">
          <mxGeometry x="310" y="40" width="60" height="60" as="geometry" />
        </mxCell>
        <mxCell id="eu-er-lbl" value="er-circuit-eu-primary" style="text;html=1;strokeColor=none;fillColor=none;align=center;fontSize=9;" vertex="1" parent="eu-vnet">
          <mxGeometry x="275" y="103" width="130" height="16" as="geometry" />
        </mxCell>

        <!-- Azure Virtual WAN Hub -->
        <mxCell id="eu-vwan" value="Azure Virtual WAN&amp;#xa;Global Backbone Hub" style="shape=mxgraph.azure.virtual_wan;fillColor=#0078D4;strokeColor=#ffffff;fontColor=#032D60;fontStyle=1;labelBackgroundColor=none;" vertex="1" parent="eu-vnet">
          <mxGeometry x="530" y="40" width="60" height="60" as="geometry" />
        </mxCell>
        <mxCell id="eu-vwan-lbl" value="vwan-hub-eu-sovereign" style="text;html=1;strokeColor=none;fillColor=none;align=center;fontSize=9;" vertex="1" parent="eu-vnet">
          <mxGeometry x="490" y="103" width="140" height="16" as="geometry" />
        </mxCell>

        <!-- Azure Front Door -->
        <mxCell id="eu-afd" value="Azure Front Door" style="shape=mxgraph.azure.azure_front_door_service;fillColor=#0078D4;strokeColor=#ffffff;fontColor=#032D60;fontStyle=1;labelBackgroundColor=none;" vertex="1" parent="eu-vnet">
          <mxGeometry x="100" y="40" width="60" height="60" as="geometry" />
        </mxCell>

        <!-- EU Public Subnet -->
        <mxCell id="eu-pub-sub" value="Public Subnet &amp;mdash; 172.16.1.0/24  (Zone: West Europe)" style="shape=mxgraph.azure.subnet;strokeColor=#0078D4;fillColor=#DAEEFA;fontStyle=1;fontSize=10;verticalAlign=top;spacingTop=4;whiteSpace=wrap;html=1;" vertex="1" parent="eu-vnet">
          <mxGeometry x="30" y="140" width="660" height="170" as="geometry" />
        </mxCell>
        <mxCell id="eu-agw" value="App Gateway WAF v2" style="shape=mxgraph.azure.application_gateway;fillColor=#0078D4;strokeColor=#ffffff;fontColor=#032D60;fontStyle=1;labelBackgroundColor=none;" vertex="1" parent="eu-pub-sub">
          <mxGeometry x="30" y="60" width="60" height="60" as="geometry" />
        </mxCell>
        <mxCell id="eu-ddos" value="Azure DDoS Standard" style="shape=mxgraph.azure.ddos_protection_plans;fillColor=#DD344C;strokeColor=#ffffff;fontColor=#032D60;fontStyle=1;labelBackgroundColor=none;" vertex="1" parent="eu-pub-sub">
          <mxGeometry x="200" y="60" width="60" height="60" as="geometry" />
        </mxCell>
        <mxCell id="eu-nat" value="Azure NAT Gateway" style="shape=mxgraph.azure.nat_gateway;fillColor=#0078D4;strokeColor=#ffffff;fontColor=#032D60;fontStyle=1;labelBackgroundColor=none;" vertex="1" parent="eu-pub-sub">
          <mxGeometry x="390" y="60" width="60" height="60" as="geometry" />
        </mxCell>
        <mxCell id="eu-nat-lbl" value="nat-gw-eu (PIP: 20.xx.xx.xx)" style="text;html=1;strokeColor=none;fillColor=none;align=center;fontSize=9;" vertex="1" parent="eu-pub-sub">
          <mxGeometry x="360" y="123" width="130" height="16" as="geometry" />
        </mxCell>
        <mxCell id="eu-tm" value="Traffic Manager&amp;#xa;GeoDNS Routing" style="shape=mxgraph.azure.traffic_manager_profiles;fillColor=#0078D4;strokeColor=#ffffff;fontColor=#032D60;fontStyle=1;labelBackgroundColor=none;" vertex="1" parent="eu-pub-sub">
          <mxGeometry x="560" y="60" width="60" height="60" as="geometry" />
        </mxCell>

        <!-- EU Private App Subnet -->
        <mxCell id="eu-app-sub" value="Private App Subnet &amp;mdash; 172.16.2.0/24  (Zone 1 / Zone 2)" style="shape=mxgraph.azure.subnet;strokeColor=#0078D4;fillColor=#CCE5F5;fontStyle=1;fontSize=10;verticalAlign=top;spacingTop=4;whiteSpace=wrap;html=1;" vertex="1" parent="eu-vnet">
          <mxGeometry x="30" y="340" width="660" height="310" as="geometry" />
        </mxCell>
        <mxCell id="eu-aks" value="Azure AKS Cluster&amp;#xa;LangGraph + Presidio&amp;#xa;+ Envoy Gateway" style="shape=mxgraph.azure.kubernetes_service;fillColor=#0078D4;strokeColor=#ffffff;fontColor=#032D60;fontStyle=1;labelBackgroundColor=none;" vertex="1" parent="eu-app-sub">
          <mxGeometry x="30" y="55" width="65" height="65" as="geometry" />
        </mxCell>
        <mxCell id="eu-aks-lbl" value="aks-eu-prod&amp;#xa;Zone 1+2, D8s_v5" style="text;html=1;strokeColor=none;fillColor=none;align=center;fontSize=9;" vertex="1" parent="eu-app-sub">
          <mxGeometry x="5" y="123" width="115" height="28" as="geometry" />
        </mxCell>
        <mxCell id="eu-gpu" value="GPU Node Pool&amp;#xa;NC24s_v3&amp;#xa;vLLM EU Sovereign" style="shape=mxgraph.azure.virtual_machine;fillColor=#0078D4;strokeColor=#ffffff;fontColor=#032D60;fontStyle=1;labelBackgroundColor=none;" vertex="1" parent="eu-app-sub">
          <mxGeometry x="200" y="55" width="65" height="65" as="geometry" />
        </mxCell>
        <mxCell id="eu-apim" value="Azure API Mgmt&amp;#xa;OAuth2 / JWT" style="shape=mxgraph.azure.api_management;fillColor=#0078D4;strokeColor=#ffffff;fontColor=#032D60;fontStyle=1;labelBackgroundColor=none;" vertex="1" parent="eu-app-sub">
          <mxGeometry x="390" y="55" width="65" height="65" as="geometry" />
        </mxCell>
        <mxCell id="eu-oai" value="Azure OpenAI&amp;#xa;EU Private Endpoint" style="shape=mxgraph.azure.cognitive_services;fillColor=#0078D4;strokeColor=#ffffff;fontColor=#032D60;fontStyle=1;labelBackgroundColor=none;" vertex="1" parent="eu-app-sub">
          <mxGeometry x="560" y="55" width="65" height="65" as="geometry" />
        </mxCell>
        <mxCell id="eu-redis" value="Azure Cache Redis&amp;#xa;Semantic Cache" style="shape=mxgraph.azure.azure_cache_for_redis;fillColor=#C7131F;strokeColor=#ffffff;fontColor=#032D60;fontStyle=1;labelBackgroundColor=none;" vertex="1" parent="eu-app-sub">
          <mxGeometry x="30" y="195" width="65" height="65" as="geometry" />
        </mxCell>
        <mxCell id="eu-func" value="Azure Functions&amp;#xa;Event Trigger" style="shape=mxgraph.azure.function_apps;fillColor=#0078D4;strokeColor=#ffffff;fontColor=#032D60;fontStyle=1;labelBackgroundColor=none;" vertex="1" parent="eu-app-sub">
          <mxGeometry x="200" y="195" width="65" height="65" as="geometry" />
        </mxCell>

        <!-- EU Private Data Subnet -->
        <mxCell id="eu-data-sub" value="Private Data Subnet &amp;mdash; 172.16.3.0/24  (Zone 1 / 2 / 3)" style="shape=mxgraph.azure.subnet;strokeColor=#0078D4;fillColor=#BFDBF0;fontStyle=1;fontSize=10;verticalAlign=top;spacingTop=4;whiteSpace=wrap;html=1;" vertex="1" parent="eu-vnet">
          <mxGeometry x="30" y="680" width="660" height="240" as="geometry" />
        </mxCell>
        <mxCell id="eu-search" value="Azure AI Search&amp;#xa;EU Sovereign Vector" style="shape=mxgraph.azure.search;fillColor=#0078D4;strokeColor=#ffffff;fontColor=#032D60;fontStyle=1;labelBackgroundColor=none;" vertex="1" parent="eu-data-sub">
          <mxGeometry x="30" y="70" width="65" height="65" as="geometry" />
        </mxCell>
        <mxCell id="eu-pg" value="Azure PostgreSQL&amp;#xa;Flexible CMK" style="shape=mxgraph.azure.azure_database_postgresql;fillColor=#0078D4;strokeColor=#ffffff;fontColor=#032D60;fontStyle=1;labelBackgroundColor=none;" vertex="1" parent="eu-data-sub">
          <mxGeometry x="200" y="70" width="65" height="65" as="geometry" />
        </mxCell>
        <mxCell id="eu-blob" value="Azure Blob Storage&amp;#xa;GDPR CMK" style="shape=mxgraph.azure.storage_accounts;fillColor=#0078D4;strokeColor=#ffffff;fontColor=#032D60;fontStyle=1;labelBackgroundColor=none;" vertex="1" parent="eu-data-sub">
          <mxGeometry x="390" y="70" width="65" height="65" as="geometry" />
        </mxCell>
        <mxCell id="eu-kv" value="Azure Key Vault HSM&amp;#xa;Customer Managed Key" style="shape=mxgraph.azure.key_vaults;fillColor=#DD344C;strokeColor=#ffffff;fontColor=#032D60;fontStyle=1;labelBackgroundColor=none;" vertex="1" parent="eu-data-sub">
          <mxGeometry x="560" y="70" width="65" height="65" as="geometry" />
        </mxCell>

        <!-- EU On-Premises -->
        <mxCell id="eu-onprem" value="On-Premises DC&amp;#xa;MPLS / Leased Line" style="shape=mxgraph.azure.server;fillColor=#687078;strokeColor=#ffffff;fontColor=#ffffff;fontStyle=1;labelBackgroundColor=none;" vertex="1" parent="eu-vnet">
          <mxGeometry x="30" y="980" width="65" height="65" as="geometry" />
        </mxCell>
        <mxCell id="eu-onprem-lbl" value="corp-dc-eu (via ExpressRoute)" style="text;html=1;strokeColor=none;fillColor=none;align=center;fontSize=9;" vertex="1" parent="eu-vnet">
          <mxGeometry x="0" y="1048" width="130" height="16" as="geometry" />
        </mxCell>
        <mxCell id="eu-mon" value="Azure Monitor + Log Analytics&amp;#xa;(GDPR / EU AI Act Audit Trail)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#032D60;strokeColor=#0078D4;fontColor=#0078D4;fontStyle=1;fontSize=9;" vertex="1" parent="eu-vnet">
          <mxGeometry x="390" y="980" width="280" height="50" as="geometry" />
        </mxCell>

        <!-- ================================================================ -->
        <!-- REGION 3: AWS ap-southeast-1  APAC Sovereign Hub (VPC)         -->
        <!-- ================================================================ -->
        <mxCell id="apac-vpc" value="AWS VPC &amp;mdash; ap-southeast-1  (10.1.0.0/16)&amp;#xa;APAC Sovereign Hub | MAS TRM / HKMA Compliant" style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc;strokeColor=#3F8624;fillColor=#F0F9F0;fontStyle=1;fontSize=11;fontColor=#232F3E;whiteSpace=wrap;html=1;verticalAlign=top;align=center;spacingTop=5;" vertex="1" parent="1">
          <mxGeometry x="1590" y="30" width="720" height="1220" as="geometry" />
        </mxCell>

        <!-- APAC IGW -->
        <mxCell id="apac-igw" value="Internet Gateway" style="shape=mxgraph.aws4.internet_gateway;fillColor=#3F8624;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="apac-vpc">
          <mxGeometry x="100" y="40" width="60" height="60" as="geometry" />
        </mxCell>
        <mxCell id="apac-igw-lbl" value="igw-apac-prod" style="text;html=1;strokeColor=none;fillColor=none;align=center;fontSize=9;" vertex="1" parent="apac-vpc">
          <mxGeometry x="75" y="103" width="110" height="16" as="geometry" />
        </mxCell>

        <!-- APAC Direct Connect -->
        <mxCell id="apac-dx" value="AWS Direct Connect&amp;#xa;SG-AP 10 Gbps" style="shape=mxgraph.aws4.direct_connect;fillColor=#3F8624;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="apac-vpc">
          <mxGeometry x="310" y="40" width="60" height="60" as="geometry" />
        </mxCell>

        <!-- APAC Transit Gateway -->
        <mxCell id="apac-tgw" value="Transit Gateway&amp;#xa;(10.1.0.0/8 RT)" style="shape=mxgraph.aws4.transit_gateway;fillColor=#3F8624;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="apac-vpc">
          <mxGeometry x="530" y="40" width="60" height="60" as="geometry" />
        </mxCell>
        <mxCell id="apac-tgw-lbl" value="tgw-apac-global-backbone" style="text;html=1;strokeColor=none;fillColor=none;align=center;fontSize=9;" vertex="1" parent="apac-vpc">
          <mxGeometry x="490" y="103" width="145" height="16" as="geometry" />
        </mxCell>

        <!-- APAC Public Subnet -->
        <mxCell id="apac-pub-sub" value="Public Subnet &amp;mdash; 10.1.1.0/24  (AZ: ap-southeast-1a)" style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_subnet;strokeColor=#3F8624;fillColor=#E6F5E6;fontStyle=1;fontSize=10;verticalAlign=top;spacingTop=4;whiteSpace=wrap;html=1;" vertex="1" parent="apac-vpc">
          <mxGeometry x="30" y="140" width="660" height="170" as="geometry" />
        </mxCell>
        <mxCell id="apac-alb" value="App Load Balancer" style="shape=mxgraph.aws4.application_load_balancer;fillColor=#3F8624;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="apac-pub-sub">
          <mxGeometry x="30" y="60" width="60" height="60" as="geometry" />
        </mxCell>
        <mxCell id="apac-waf" value="AWS WAF v2" style="shape=mxgraph.aws4.shield;fillColor=#DD344C;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="apac-pub-sub">
          <mxGeometry x="200" y="60" width="60" height="60" as="geometry" />
        </mxCell>
        <mxCell id="apac-nat" value="NAT Gateway" style="shape=mxgraph.aws4.nat_gateway;fillColor=#3F8624;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="apac-pub-sub">
          <mxGeometry x="390" y="60" width="60" height="60" as="geometry" />
        </mxCell>
        <mxCell id="apac-nat-lbl" value="nat-gw-apac (EIP: 13.xx.xx.xx)" style="text;html=1;strokeColor=none;fillColor=none;align=center;fontSize=9;" vertex="1" parent="apac-pub-sub">
          <mxGeometry x="360" y="123" width="135" height="16" as="geometry" />
        </mxCell>
        <mxCell id="apac-r53" value="Route 53&amp;#xa;Health Check" style="shape=mxgraph.aws4.route_53;fillColor=#3F8624;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="apac-pub-sub">
          <mxGeometry x="555" y="60" width="60" height="60" as="geometry" />
        </mxCell>

        <!-- APAC Private App Subnet -->
        <mxCell id="apac-app-sub" value="Private App Subnet &amp;mdash; 10.1.2.0/24  (AZ: ap-southeast-1a / 1b)" style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_subnet;strokeColor=#3F8624;fillColor=#DDF0DD;fontStyle=1;fontSize=10;verticalAlign=top;spacingTop=4;whiteSpace=wrap;html=1;" vertex="1" parent="apac-vpc">
          <mxGeometry x="30" y="340" width="660" height="310" as="geometry" />
        </mxCell>
        <mxCell id="apac-eks" value="Amazon EKS Cluster&amp;#xa;LangGraph + LiteLLM&amp;#xa;+ Envoy Gateway" style="shape=mxgraph.aws4.eks;fillColor=#F58534;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="apac-app-sub">
          <mxGeometry x="30" y="55" width="65" height="65" as="geometry" />
        </mxCell>
        <mxCell id="apac-eks-lbl" value="eks-apac-prod&amp;#xa;2 AZs, m5.4xlarge" style="text;html=1;strokeColor=none;fillColor=none;align=center;fontSize=9;" vertex="1" parent="apac-app-sub">
          <mxGeometry x="5" y="123" width="115" height="28" as="geometry" />
        </mxCell>
        <mxCell id="apac-gpu" value="GPU Node Group&amp;#xa;4x NVIDIA A10G&amp;#xa;vLLM MAS TRM Local" style="shape=mxgraph.aws4.ec2;fillColor=#F58534;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="apac-app-sub">
          <mxGeometry x="200" y="55" width="65" height="65" as="geometry" />
        </mxCell>
        <mxCell id="apac-apigw" value="API Gateway&amp;#xa;REST + WebSocket" style="shape=mxgraph.aws4.api_gateway;fillColor=#E7157B;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="apac-app-sub">
          <mxGeometry x="390" y="55" width="65" height="65" as="geometry" />
        </mxCell>
        <mxCell id="apac-bedrock" value="AWS Bedrock&amp;#xa;ap-southeast-1&amp;#xa;Zero-Retention" style="shape=mxgraph.aws4.sagemaker;fillColor=#01A88D;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="apac-app-sub">
          <mxGeometry x="560" y="55" width="65" height="65" as="geometry" />
        </mxCell>
        <mxCell id="apac-redis" value="ElastiCache Redis&amp;#xa;Semantic Cache" style="shape=mxgraph.aws4.elasticache;fillColor=#C7131F;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="apac-app-sub">
          <mxGeometry x="30" y="195" width="65" height="65" as="geometry" />
        </mxCell>
        <mxCell id="apac-sm" value="SageMaker&amp;#xa;Embedding Svc" style="shape=mxgraph.aws4.sagemaker;fillColor=#01A88D;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="apac-app-sub">
          <mxGeometry x="200" y="195" width="65" height="65" as="geometry" />
        </mxCell>

        <!-- APAC Private Data Subnet -->
        <mxCell id="apac-data-sub" value="Private Data Subnet &amp;mdash; 10.1.3.0/24  (AZ: ap-southeast-1a / 1b / 1c)" style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_subnet;strokeColor=#3F8624;fillColor=#CCE8CC;fontStyle=1;fontSize=10;verticalAlign=top;spacingTop=4;whiteSpace=wrap;html=1;" vertex="1" parent="apac-vpc">
          <mxGeometry x="30" y="680" width="660" height="240" as="geometry" />
        </mxCell>
        <mxCell id="apac-opensearch" value="Amazon OpenSearch&amp;#xa;HNSW Vector + BM25" style="shape=mxgraph.aws4.opensearch_service;fillColor=#8C4FFF;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="apac-data-sub">
          <mxGeometry x="30" y="70" width="65" height="65" as="geometry" />
        </mxCell>
        <mxCell id="apac-rds" value="RDS PostgreSQL&amp;#xa;Multi-AZ CMK" style="shape=mxgraph.aws4.rds;fillColor=#C7131F;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="apac-data-sub">
          <mxGeometry x="200" y="70" width="65" height="65" as="geometry" />
        </mxCell>
        <mxCell id="apac-s3" value="S3 Sovereign&amp;#xa;KMS CMK AES-256" style="shape=mxgraph.aws4.s3;fillColor=#3F8624;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="apac-data-sub">
          <mxGeometry x="390" y="70" width="65" height="65" as="geometry" />
        </mxCell>
        <mxCell id="apac-kms" value="AWS KMS&amp;#xa;Customer Managed Key" style="shape=mxgraph.aws4.key_management_service;fillColor=#DD344C;strokeColor=#ffffff;fontColor=#232F3E;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="apac-data-sub">
          <mxGeometry x="560" y="70" width="65" height="65" as="geometry" />
        </mxCell>

        <!-- APAC On-Premises -->
        <mxCell id="apac-onprem" value="On-Premises DC&amp;#xa;SG Leased Line" style="shape=mxgraph.aws4.traditional_server;fillColor=#687078;strokeColor=#ffffff;fontColor=#ffffff;fontStyle=1;labelBackgroundColor=none;sketch=0;" vertex="1" parent="apac-vpc">
          <mxGeometry x="30" y="980" width="65" height="65" as="geometry" />
        </mxCell>
        <mxCell id="apac-cw" value="CloudWatch + VPC Flow Logs&amp;#xa;(MAS TRM / HKMA Audit)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#232F3E;strokeColor=#FF9900;fontColor=#FF9900;fontStyle=1;fontSize=9;" vertex="1" parent="apac-vpc">
          <mxGeometry x="390" y="980" width="280" height="50" as="geometry" />
        </mxCell>

        <!-- ================================================================ -->
        <!-- GLOBAL  Cloudflare GeoDNS + Anycast WAF                         -->
        <!-- ================================================================ -->
        <mxCell id="cloudflare" value="Cloudflare Enterprise WAF + GeoDNS + Anycast&amp;#xa;Global Traffic Steering to Nearest Sovereign Region" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F48024;strokeColor=#c46d11;fontStyle=1;fontColor=#ffffff;fontSize=11;" vertex="1" parent="1">
          <mxGeometry x="890" y="1280" width="540" height="55" as="geometry" />
        </mxCell>

        <!-- ================================================================ -->
        <!-- CROSS-REGION BACKBONE CONNECTIONS                               -->
        <!-- ================================================================ -->
        <mxCell id="link-na-eu" value="TGW to VNet Peering&amp;#xa;Metadata Only - No PII Crosses&amp;#xa;Direct Connect + ExpressRoute" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthoLoop=1;jettySize=auto;html=1;strokeColor=#8C4FFF;strokeWidth=3;dashed=1;endArrow=block;startArrow=block;endFill=1;startFill=1;fontSize=10;fontColor=#8C4FFF;" edge="1" parent="1" source="na-tgw" target="eu-vwan">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="link-eu-apac" value="VWan to TGW Peering&amp;#xa;Metadata Only - No PII Crosses&amp;#xa;ExpressRoute + Direct Connect" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthoLoop=1;jettySize=auto;html=1;strokeColor=#0078D4;strokeWidth=3;dashed=1;endArrow=block;startArrow=block;endFill=1;startFill=1;fontSize=10;fontColor=#0078D4;" edge="1" parent="1" source="eu-vwan" target="apac-tgw">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="link-na-apac" value="TGW to TGW Inter-Region&amp;#xa;AWS Global Accelerator&amp;#xa;Metadata Only - No PII" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthoLoop=1;jettySize=auto;html=1;strokeColor=#3F8624;strokeWidth=2;dashed=1;endArrow=block;startArrow=block;endFill=1;startFill=1;fontSize=10;fontColor=#3F8624;" edge="1" parent="1" source="na-tgw" target="apac-tgw">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="cf-na" value="Internet" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=#F48024;strokeWidth=2;" edge="1" parent="1" source="cloudflare" target="na-igw">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="cf-eu" value="Internet" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=#F48024;strokeWidth=2;" edge="1" parent="1" source="cloudflare" target="eu-afd">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="cf-apac" value="Internet" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=#F48024;strokeWidth=2;" edge="1" parent="1" source="cloudflare" target="apac-igw">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>'''

# Read file
with open(DRAWIO_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# Find old Page 2 boundaries
start_marker = '  <!-- Page 2: Multi-Region Sovereign Infrastructure View -->'
end_marker   = '  <!-- Page 3: Security & Privacy View -->'

start_idx = content.find(start_marker)
end_idx   = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print(f"ERROR: Could not locate Page 2 boundaries.")
    print(f"  start_marker found: {start_idx != -1}")
    print(f"  end_marker found:   {end_idx != -1}")
    exit(1)

print(f"Found Page 2 from char {start_idx} to {end_idx}")
print(f"Old Page 2 length: {end_idx - start_idx} chars")

# Build replacement: new page2 + a blank line before Page 3
new_content = (
    content[:start_idx]
    + NEW_PAGE2
    + '\n\n'
    + content[end_idx:]
)

# Write back
with open(DRAWIO_PATH, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"Done! New file length: {len(new_content)} chars / {new_content.count(chr(10))} lines")

# Verify
with open(DRAWIO_PATH, 'r', encoding='utf-8') as f:
    verify = f.read()

checks = [
    ('mxgraph.aws4.internet_gateway', 'AWS Internet Gateway icon'),
    ('mxgraph.aws4.transit_gateway',  'AWS Transit Gateway icon'),
    ('mxgraph.aws4.direct_connect',   'AWS Direct Connect icon'),
    ('mxgraph.aws4.nat_gateway',      'AWS NAT Gateway icon'),
    ('mxgraph.aws4.eks',              'AWS EKS icon'),
    ('mxgraph.aws4.opensearch_service','AWS OpenSearch icon'),
    ('mxgraph.aws4.rds',              'AWS RDS icon'),
    ('mxgraph.aws4.s3',               'AWS S3 icon'),
    ('mxgraph.aws4.key_management_service', 'AWS KMS icon'),
    ('mxgraph.azure.expressroute',    'Azure ExpressRoute icon'),
    ('mxgraph.azure.virtual_wan',     'Azure Virtual WAN icon'),
    ('mxgraph.azure.nat_gateway',     'Azure NAT Gateway icon'),
    ('mxgraph.azure.kubernetes_service','Azure AKS icon'),
    ('mxgraph.azure.application_gateway','Azure App Gateway icon'),
    ('mxgraph.azure.cognitive_services','Azure OpenAI icon'),
    ('mxgraph.azure.key_vaults',      'Azure Key Vault icon'),
    ('group_subnet',                  'Subnet groups'),
    ('group_vpc',                     'VPC groups'),
    ('na-tgw',                        'NA TGW node'),
    ('eu-vwan',                       'EU VWan node'),
    ('apac-tgw',                      'APAC TGW node'),
    ('link-na-eu',                    'NA-EU backbone link'),
    ('link-eu-apac',                  'EU-APAC backbone link'),
    ('link-na-apac',                  'NA-APAC backbone link'),
]

print('\n--- Verification ---')
all_ok = True
for key, label in checks:
    found = key in verify
    status = 'OK  ' if found else 'FAIL'
    if not found:
        all_ok = False
    print(f"  {status}  {label}")

if all_ok:
    print('\nAll checks passed!')
else:
    print('\nSome checks FAILED - review the output above.')
