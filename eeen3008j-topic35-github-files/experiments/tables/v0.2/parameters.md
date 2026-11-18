# v0.2 参数表（报告可用）

全部自选物理参数为 illustrative；统计规模来自2026-11-03组内协调，不是老师额外要求。

| Parameter | Value | Status / source |
|---|---|---|
| State / predictor | 1D position; timestamped constant velocity | Topic 35 + group abstraction |
| Observation / clock | Exact position and velocity; shared clock | Illustrative idealization |
| Duration / step | 60 s / 0.01 s | Group frozen setting |
| Initial state | p=0 m, v=1 m/s, shared exactly | Common initial condition; initialization bytes excluded |
| Velocity increment magnitude | 0, 0.5, 1, 2 m/s | Illustrative main sweep |
| Manoeuvre timing | One jump per 2 s interval; start+U(0.1,1.8) s | Illustrative analytic trace; grid rounded |
| Data loss probability | 0, 0.1, 0.3 | Illustrative time-indexed Bernoulli trace |
| Data / ACK packet | 32 / 16 B | Logical bytes, not full air-interface overhead |
| Link service rate | 3200 bit/s | Illustrative stop-and-wait service |
| Data / ACK service | 0.08 / 0.04 s | Derived from bytes and service rate |
| Forward / ACK extra delay | 0.05 / 0.02 s | Illustrative; additional to service |
| Queue / feedback | No queue; reliable delayed ACK | Frozen abstraction |
| Period / age threshold | 0.25, 0.5, 1, 2, 4 s | Predeclared for all relevant policies |
| Error threshold | 0.05, 0.1, 0.2, 0.5, 1 m | Predeclared E and EA |
| Error tolerance | 0.5 m | Evaluation, distinct from trigger threshold |
| Tuning / evaluation | seeds 0–9 / 100–129 | Independent sets, common traces within seed |
| Uncertainty | 10000 seed bootstrap samples; 95% percentile intervals | n=30 per workpoint; no simultaneous coverage |
| Tuning budgets | 24 / 48 / 96 B/s | Mean tuning constraint; not a hard evaluation budget |

Machine-readable source: `../../configs/formal_v02.json`; equations and precise event order: `../../experiment_spec_v02.md`.
