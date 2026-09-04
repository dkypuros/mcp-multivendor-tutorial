# The Timestamp Path

[`timing_fault_explained.md`](timing_fault_explained.md) tells the story of the fault;
this page maps the machinery it travels through. Nine components touch a PTP timestamp between
the Grandmaster and the radio, spanning silicon, kernel, userspace, platform, and orchestration —
and the incident at the heart of this tutorial is a failure in exactly one of them.

<img src="diagrams/timestamp_path.svg" alt="Sequence diagram: the PTP timestamp path from Grandmaster through NIC, PHC, kernel, ptp4l, PTP operator, event proxy, and DU to the orchestrator, with normal and incident branches and the multi-agent RCA band" width="960" />

Print/download version: [`diagrams/timestamp_path.pdf`](diagrams/timestamp_path.pdf)
(A3 landscape; TikZ source in [`diagrams/src/`](diagrams/src/)).

## The lanes, top to bottom of the stack

Reading left to right, each lifeline owns one narrow piece of the truth:

- **Telecom Grandmaster (T-GM)** — the reference clock, typically GNSS-disciplined, profiled
  under ITU-T G.8275.1 for full on-path support.
- **NIC (e.g. Intel E810, `ice` driver)** — where hardware timestamping happens: the departure
  or arrival instant of a PTP packet is latched *at the MAC boundary*, below anything software
  can perturb. This lane is where our incident lives.
- **PTP Hardware Clock (PHC)** — the NIC's own adjustable clock, exposed to Linux as
  `/dev/ptpN`; the entity `ptp4l` actually steers.
- **Linux kernel** — transports timestamps to userspace via `SO_TIMESTAMPING` socket options:
  ingress stamps ride as ancillary data, egress stamps come back on the socket *error queue* —
  a detail that matters in the incident branch, because a late egress stamp is a stamp that
  arrives on that queue after its packet's context is gone.
- **`ptp4l` (userspace servo)** — computes path delay and master offset from the
  Sync/Follow_Up exchanges and disciplines the PHC; reports LOCKED while the loop holds.
- **PTP Operator (platform)** — the Kubernetes-side management layer that runs and watches the
  daemons and exposes timing state as platform status.
- **Cloud Event Proxy** — turns timing state changes into CloudEvents
  (`event.ptp.sync.state-change`) that the rest of the cluster can subscribe to.
- **O-DU (S-plane consumer)** — the radio-side consumer of synchronization: while timing is
  good it aligns TDD frames; when its S-plane holdover budget is exhausted it takes the carrier
  down, per the protective behavior described in
  [`timing_fault_explained.md`](timing_fault_explained.md).
- **Orchestrator / fault management** — receives the alert and, in this tutorial's pattern,
  conducts the multi-agent RCA.

## The two branches

The **green branch** is the steady state, and part of it runs live in the environment behind
this repository: the servo loop computing path delay and master offset is a real pair of
`ptp4l` instances, and the convergence series in
[`data/ptp_offset_samples.jsonl`](data/ptp_offset_samples.jsonl) —
`phc_offset_ns` walking from −6,253 to −5,032 over thirty seconds — is that loop, measured
while LOCKED.

The **red branch** changes exactly one arrow. The servo requests the egress hardware timestamp
for Sync X and the NIC's timestamping unit misses it (`tx_hwtstamp_timeout`). Everything after
that is correct behavior on bad input: the stale stamp surfaces in the next packet window and
gets associated with seq X+1, the path-delay calculation ingests mis-matched evidence, the
offset spikes by milliseconds, the servo drops to FREERUN, the anomaly is published, the DU
exhausts its holdover budget and takes the cell down. The captured record of this branch —
injected and observed live, end to end — is
[`data/incident_capture.jsonl`](data/incident_capture.jsonl): eight timestamped snapshots from
`port_state: LOCKED` through `FREERUN`, the orchestrator's view, its decision, and the heal
back to `LOCKED`.

## The purple band: where it becomes multivendor

The three extractions at the bottom — driver debug log, lock-state history, S-plane impact —
land in three different organizations' domains. That is the entire reason they run as
**authorized MCP tool calls through the gateway**
([`kuadrant_authorino_mcp_gateway.md`](kuadrant_authorino_mcp_gateway.md)) rather than as
shared dashboards: each party answers questions about its own domain with structured testimony,
and the orchestrator corroborates before concluding
([`multivendor_rca_pattern.md`](multivendor_rca_pattern.md)). In the captured incident the
corroboration fell below the bar and the recorded decision is
`"HOLD — below the bar, a human signs"` — visible verbatim in the dataset.

## Reproducing the capture

[`../scripts/capture_incident.py`](../scripts/capture_incident.py) produces a dataset of the
same shape against any conforming endpoints, wired through the environment contract in
[`.env.example`](../.env.example). It performs the same eight steps — nominal, inject, faulted,
events, orchestrator view, RCA, heal, restored — and writes one JSON record per step.
