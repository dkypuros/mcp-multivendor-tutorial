# The Anatomy of a Timing Fault — a Plain-Prose Explainer

This page explains, without assuming any telco background, why the fault at the center of this
tutorial's RCA scenario ([`multivendor_rca_pattern.md`](multivendor_rca_pattern.md)) is such a
perfect teaching case for multivendor diagnosis. Nothing here is vendor-specific; every mechanism
described is from public standards (IEEE 1588, 3GPP, O-RAN).

## Why a radio network cares about nanoseconds

A 5G radio network is a room full of transmitters that must take turns with exquisite precision.
In TDD (time-division duplex) radio, downlink and uplink share the same frequency and are
separated only *in time* — the base station transmits, then listens, thousands of times per
second. If two neighboring cells disagree about what time it is by even a few microseconds, one
cell's "transmit" overlaps another's "listen," and they jam each other. The 3GPP specification
(TS 38.104) allows roughly **1.5 microseconds** of misalignment. Beyond that, a cell must not
transmit at all — a silent cell is better than a jamming one.

So every radio unit needs a clock, and all the clocks must agree. That agreement is delivered by
the **Precision Time Protocol** (PTP, IEEE 1588): one device, the **Grandmaster**, owns the
reference time, and every downstream clock disciplines itself to it, continuously, over the
network.

## How PTP moves time across a wire

You cannot simply *send* the time in a packet — by the time the packet arrives, the time it
carries is stale by however long the trip took. PTP solves this with a two-message pattern:

1. The Grandmaster sends a **Sync** message. The precise instant it leaves the hardware is
   captured by the network card itself — a **hardware timestamp**, taken at the physical layer,
   far more exact than anything software could measure.
2. That captured timestamp travels in a **Follow_Up** message right behind the Sync.

The receiver combines the two — "the Sync left at exactly T, and I received it at T+x" — and,
with the return-trip messages, computes both the link delay and its own clock error. A servo
loop then nudges the local clock into agreement, typically to within tens of nanoseconds. While
the loop converges and holds, the clock is **LOCKED**. If the reference disappears or turns
inconsistent, the clock keeps running on its own oscillator — **FREERUN** — drifting further
from the truth every second. LOCKED ↔ FREERUN is the single most important status word in this
whole scenario.

## The fault: a hardware timestamp that never arrived

Now the actual failure this tutorial's demo injects — modeled on a class of fault documented
publicly in the industry:

The Grandmaster's network card is asked for the egress hardware timestamp of Sync X — and
**doesn't produce it in time**. The timestamping unit on the NIC times out. What happens next is
a cascade in which *every component behaves correctly and the system still fails*:

- With no timestamp for Sync X, the Grandmaster never sends Follow_Up X. Or worse: the stale
  timestamp finally pops out of the hardware queue and gets matched to the *next* window, so
  Follow_Up X+1 goes out carrying **the previous Sync's origin time**.
- The receiving clock does the arithmetic in good faith on bad data and computes a wild offset —
  tens of milliseconds, where the tolerance is 1.5 microseconds.
- The servo declares the reference untrustworthy: **LOCKED → FREERUN**.
- The radio unit, now unsure of its timing, follows the standard's rule: it raises a
  `lossOfRealTimeSynchronization` alarm (3GPP TS 28.532) and **shuts down its own RF carrier**
  to avoid interfering with neighbors. The cell goes dark.
- Every phone on that cell loses signal, declares radio link failure, and tries to reattach —
  to a cell that will not answer.

## Why no single party can diagnose it

Trace the evidence backward and notice who owns each piece:

- The **dead cell and the alarm** are visible to the RAN vendor.
- The **offset spike and the FREERUN transition** are visible to the platform operator's PTP
  daemons.
- The **missing Follow_Up and the stale origin timestamp** are visible only in packet-level
  forensics at the protocol layer.
- The **actual cause** — the timestamp timeout — is visible only in the NIC driver's counters
  and the kernel log, which belong to the silicon vendor.

The party experiencing the outage (the RAN) holds none of the root-cause evidence. The party
holding the root-cause evidence (the NIC) never sees an outage — a counter ticked from 0 to 1.
Each party's view is real, correct, and insufficient. That is why the diagnosis has to be
*orchestrated*: an agent that can ask each domain for structured testimony, corroborate the
answers, and only then conclude — which is exactly the pattern the
[evidence-chain document](multivendor_rca_pattern.md) formalizes, with the
[MCP gateway](kuadrant_authorino_mcp_gateway.md) making each of those cross-vendor questions
authenticated, rate-limited, and audited.

## The vocabulary, in one place

| Term | Plain meaning |
|------|---------------|
| **PTP / IEEE 1588** | The protocol that carries time across a network from one reference clock to many |
| **Grandmaster (GM)** | The device that owns the reference time |
| **Sync / Follow_Up** | The message pair: Sync marks the moment, Follow_Up carries the hardware-captured timestamp of that moment |
| **Hardware timestamp** | The departure/arrival time captured by the NIC itself at the physical layer |
| **Servo** | The control loop that steers a local clock toward the reference |
| **LOCKED / FREERUN** | Servo states: disciplined to the reference / drifting on its own |
| **master offset** | The measured error between local clock and reference |
| **`lossOfRealTimeSynchronization`** | The standard alarm (3GPP TS 28.532) a radio unit raises when it can no longer trust its clock |
| **RF carrier shutdown** | The protective response: a cell that can't keep time stops transmitting rather than jam its neighbors |
