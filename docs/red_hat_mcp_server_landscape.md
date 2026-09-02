# Red Hat MCP Server Landscape and API Catalog

## Overview

Red Hat is building out a catalog of purpose-built MCP servers aligned to its
product portfolio. These MCP servers allow an external orchestration platform to
discover and invoke Red Hat product knowledge as discrete tools over the Model
Context Protocol, rather than integrating with a single monolithic API.

This reference documents the publicly available Red Hat APIs and MCP servers
relevant to multivendor agentic AI integration.

## Red Hat API Catalog (developers.redhat.com/api-catalog)

49 APIs currently published, organized by use case and platform. These are the
existing REST APIs that can be consumed directly or wrapped as MCP tool servers.

Source: [developers.redhat.com/api-catalog](https://developers.redhat.com/api-catalog)

### By Platform / Service

| API Name | Description | Platform | Use Case |
|----------|-------------|----------|----------|
| Advisor | Insights Advisor API | RHEL, Red Hat Lightspeed | Observe |
| Ansible automation controller API V1 | Define, operate, scale, and delegate automation | Ansible | Automation |
| Automation Hub | Fetch, upload, organize, and distribute Ansible Collections | Ansible | Automation |
| Compliance V1 | Security-policy compliance of RHEL systems | RHEL, Red Hat Lightspeed | Observe, Security |
| Compliance V2 | Security-policy compliance of RHEL systems | RHEL, Red Hat Lightspeed | Observe, Security |
| Cost Management | Project Koku and OpenShift cost management | Red Hat Lightspeed | Spend Management |
| Export Service | Export data in JSON or CSV formats | Red Hat Lightspeed | Workflows |
| Image Builder | Relay image build requests | Red Hat Lightspeed | Deploy |
| Integrations | Integrations API | Red Hat Lightspeed | Integrations and Notifications |
| Malware Detection | Detect potential malware on RHEL systems | RHEL | Observe, Security |
| Managed Inventory | Insights Platform Host Inventory | RHEL, Red Hat Lightspeed | Inventories |
| Notifications | Notifications API | Red Hat Lightspeed | Integrations and Notifications |
| Operator Gathering Conditions Service | Gathering Conditions for Insights Operator | OpenShift | Infrastructure |
| Payload Ingress Service | console.redhat.com Payload Ingress | Red Hat Lightspeed | Infrastructure |
| Red Hat Lightspeed Advisor for OpenShift V1 | Aggregation API for Insights Advisor (clusters) | Red Hat Lightspeed, OpenShift | Infrastructure, Observe |
| Red Hat Lightspeed Advisor for OpenShift V2 | Aggregation API for Insights Advisor (clusters) | Red Hat Lightspeed, OpenShift | Infrastructure, Observe |
| Patch | Patch application API | RHEL, Red Hat Lightspeed | Security, Observe |
| Playbook Dispatcher | Run Ansible Playbooks via Cloud Connector | RHEL, Red Hat Lightspeed | Automation |
| Remediations | Insights Remediations Service | RHEL | Automation, Observe |
| Resource Optimization | Resource Optimization Service | RHEL, Red Hat Lightspeed | Observe |
| Repositories | Manage content sources for console.redhat.com | RHEL, Red Hat Lightspeed | Deploy |
| Role-based Access Control | RBAC API | Red Hat Lightspeed | Identity and Access Management |
| Sources | Sources API | Red Hat Lightspeed | Identity and Access Management |
| Subscriptions Usage v1 | rhsm-subscriptions service v1 | Edge, OpenShift | Inventories, Subscriptions |
| Subscriptions Usage v2 | rhsm-subscriptions service v2 | Edge, OpenShift | Inventories, Subscriptions |
| Subscription Management | Manage Activation Keys, Manifests, Subscriptions | RHEL | Subscriptions |
| Tasks | Manage and issue Red Hat generated tasks | RHEL, Red Hat Lightspeed | Automation, Observe |
| Vulnerability Management | Vulnerability API | RHEL, Red Hat Lightspeed | Observe, Security |
| Red Hat Ansible Lightspeed | Ansible Lightspeed API | Ansible | Automation |
| Automation orchestrator | Automation component of Ansible Automation Platform | Ansible | Automation, Workflows |
| Red Hat Lightspeed for RHEL Planning | RHEL product lifecycle data | RHEL, Red Hat Lightspeed | Planning |
| Account Management Service | Manage user subscriptions and clusters | OpenShift | Infrastructure |
| Assisted-Install Service | Assisted installation | OpenShift | Infrastructure |
| Authorization Service | Access control on OCM services | OpenShift | Infrastructure |
| Clusters Management Service | Clusters Management API | OpenShift | Infrastructure |
| Connector Management | Connector Management API | OpenShift | Infrastructure |
| Image Builder Composer | Build and install images | OpenShift | Infrastructure |
| Image Builder Worker | Workers request and handle jobs | OpenShift | Infrastructure |
| OSD Fleet Manager Service | OSD Fleet Manager API | OpenShift | Infrastructure |
| Kafka Service Fleet Manager | Kafka Management API | OpenShift | Infrastructure |
| RHACS Service Fleet Manager | Manage ACS component instances | OpenShift | Infrastructure |
| Service Logs | Logs from internal sources for OpenShift clusters | OpenShift | Infrastructure |
| Access Transparency Service | Access Transparency API | OpenShift | Infrastructure |
| Service Registry Management | Manage Service Registry instances | OpenShift | Infrastructure |
| Status Board Service API | Status Board API | OpenShift | Infrastructure |
| Upgrades Information Service | Upgrades Information API | OpenShift | Infrastructure |
| Vulnerability Dashboard | OCP Vulnerability API | OpenShift, Red Hat Lightspeed | Observe, Security |
| Web-RCA Service | Web-RCA API | OpenShift | Infrastructure |
| Case Management API | Support Services Case Management | Ansible, RHEL, OpenShift | Support |

### API Count by Platform

| Platform | Count |
|----------|-------|
| OpenShift | 22 |
| Red Hat Lightspeed | 19 |
| RHEL | 16 |
| Ansible | 5 |
| Edge | 2 |

## Published MCP Servers (catalog.redhat.com)

These MCP servers are published as containerized applications on the Red Hat
Ecosystem Catalog. They are ready to deploy today.

Source: [catalog.redhat.com](https://catalog.redhat.com) (search "MCP server")

| MCP Server | Scope |
|------------|-------|
| MCP Server for RHEL | Red Hat Enterprise Linux product knowledge and operations |
| MCP Server for Red Hat OpenShift | OpenShift product knowledge and operations |
| Red Hat Lightspeed MCP Server | Red Hat Lightspeed capabilities |
| MCP Server for Red Hat Security Content | Security advisories, CVEs, vulnerability data |
| MCP Server for Red Hat Product Information | Cross-product information and lifecycle data |

## Integration Relevance for Multivendor Orchestration

In a multivendor environment, an orchestration platform connects to multiple
vendor MCP servers to query product-specific knowledge during troubleshooting,
root cause analysis, or automation. The Red Hat MCP servers most relevant to
infrastructure orchestration are:

| MCP Server | Why it matters |
|------------|---------------|
| **OpenShift** | Platform-level diagnostics, cluster health, operator status |
| **RHEL** | OS-level troubleshooting, kernel, networking, storage |
| **Security Content** | CVE lookup, security advisory correlation with running infrastructure |
| **Product Information** | Product lifecycle, version compatibility, EOL dates |
| **Case Management API** | Past resolution search for similar issues across Red Hat's support history |

### Single Agent vs Catalog of MCP Servers

| Aspect | Single Knowledge Agent | Catalog of MCP Servers |
|--------|----------------------|----------------------|
| **Integration point** | One agent, broad scope | Multiple servers, each product-scoped |
| **Protocol** | MCP (single endpoint) | MCP per server (multiple endpoints, potentially behind AI gateway) |
| **Knowledge depth** | Broad but generalized | Deep, specialized per product domain |
| **Onboarding** | One credential set | Per-server registration, or unified via AI gateway |
| **On-prem deployment** | One container to ship | Per-product containers, more granular but more to manage |
| **Offline/air-gapped** | One KB snapshot to bundle | Per-product snapshots, potentially more tractable |
