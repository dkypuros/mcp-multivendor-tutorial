# Fact Packets: the Testimony Envelope

The RCA pattern in [`multivendor_rca_pattern.md`](multivendor_rca_pattern.md) rests on one data
contract: how a specialized agent reports findings back to the orchestrator. TM Forum's
autonomous-networks work gives this object a name — a **fact packet**: a standardized container
a specialized agent uses to report factual findings to a central orchestrator (TM Forum IG1453,
Agent-to-Agent transactions). This page pins down the envelope this tutorial uses, with real
captured examples, and maps each governance property to the published standard behind it.

## The envelope

```json
{
  "plane": "hardware",
  "tool": "nic_timestamp_counters",
  "signals": ["nic_firmware_suspect"],
  "evidence": "egress HW timestamp timeout — late/stale timestamp matched to next packet window",
  "emulated": true,
  "signature": null
}
```

Field by field:

| Field | Meaning |
|-------|---------|
| `plane` | Which evidence domain this testimony belongs to (`ran`, `platform`, `hardware`, `cluster`) — the columns of the [evidence chain](diagrams/evidence_chain.svg) |
| `tool` | The MCP tool that produced it — the testimony is attributable to a specific, authorized capability, not to "the system" |
| `signals` | Machine-matchable conclusions the orchestrator's deterministic router can act on. An empty list is meaningful: *this plane saw nothing* |
| `evidence` | The human-readable finding an operator reads in the audit trail |
| `emulated` | The fidelity marker: testimony declares what kind of evidence it is. Real captures and synthesized surfaces travel in the same envelope, honestly labeled |
| `signature` | Reserved: a cryptographic signature over the packet, so the orchestrator can verify authorship and integrity — the "cryptographically signed container" of IG1453. Not yet implemented here |

Two real packets from the captured incident
([`data/incident_capture.jsonl`](data/incident_capture.jsonl)) as they appear inside the
decision object's evidence array:

```json
{"plane": "platform", "tool": "ptp_operator_status",
 "signals": ["ptp_offset_exceeded"],
 "evidence": "ptp4l MASTER, offset excursion during incident"}

{"plane": "hardware", "tool": "nic_timestamp_counters",
 "signals": ["nic_firmware_suspect"],
 "evidence": "signal: nic_firmware_suspect (Delta=74ms phase jump on dropped Follow_Up)"}
```

## The decision object that carries them

Fact packets never travel alone; they arrive assembled inside the orchestrator's auditable
conclusion — a TMF688-style event:

```json
{
  "eventType": "RcaConcludedEvent",
  "traceId": "tr-oran-tmf-…",
  "capifScope": "3gpp#mcp-aef:mcp-tools",
  "corroboration": "2/3",
  "decision": "HOLD — below the bar, a human signs",
  "planes": ["hardware", "platform"],
  "evidence": [ /* fact packets */ ]
}
```

Note what the object makes impossible to hide: which planes answered, which stayed silent, what
the corroboration count was, and that the decision followed from it. In the captured incident
the decision is a refusal — and the refusal carries its evidence just like a conclusion would.

## The standards mapping

Each governance property of this tutorial's pattern corresponds to a published TM Forum
document; the pattern is an implementation of public standards, not a private format:

| Property in this tutorial | Public standard |
|---------------------------|-----------------|
| Fact packet: signed, structured findings from specialist agent to orchestrator | **TM Forum IG1453** (Agent-to-Agent / Task transactions) |
| Per-tool policy enforcement before any agentic call (`AgentPolicy` + gateway `AuthPolicy` as the Policy Enforcement Point) | **TM Forum GB1087** (Agentic Interaction Security): authorized, sanitized, audited |
| Business intent decomposed into technical policy pushed to the network (e.g. "maintain sub-ms synchronization" → an A1 policy) | **TM Forum IG1253** (Intent Management) |
| The audit event carrying the conclusion | **TM Forum TMF688** (Event Management API) |
| The authorization scope on every tool call | **3GPP TS 29.222** (CAPIF) |

GB1087's three requirements — every agentic call **authorized** (verified against policy),
**sanitized**, and **audited** (append-only, standardized format) — map directly onto this
tutorial's three layers: the gateway's `AuthPolicy` and the in-process `AgentPolicy` CRDs
handle authorization, the gateway boundary is the sanitization point, and the TMF688-style
decision events are the audit stream. The layers weren't designed from the standard, which is
the encouraging part: independent engineering converged on the same shape the standard
prescribes.
