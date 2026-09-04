# Data captures

Live measurements referenced by the documentation.

## `ptp_offset_samples.jsonl`

Ten samples of `phc_offset_ns`, taken at ~3-second intervals from a running PTP implementation
(two `ptp4l` instances — grandmaster and DU — over a veth pair, software timestamping, mock PHC).
Referenced from [`../timing_fault_explained.md`](../timing_fault_explained.md).

The implementation's own fidelity statement, returned with every reading:

> "The PTP protocol, BMCA and port state machines are REAL (two ptp4l instances over veth); the
> accuracy is not. Offsets are millisecond-scale, not the sub-microsecond a DU requires. No DPLL,
> no GNSS, so no T-GM."

A full raw snapshot from the same surface:

```json
{
  "phc": "present",
  "phc_device": "/dev/ptp0",
  "grandmaster_daemon": "running",
  "du_daemon": "running",
  "phc2sys": "running",
  "gm_port_state": "MASTER",
  "du_port_state": "SLAVE",
  "gm_identity": "8a32c1.fffe.bf05ed",
  "phc_offset_ns": -4688,
  "timestamping": "software",
  "clock_class": "mock"
}
```
