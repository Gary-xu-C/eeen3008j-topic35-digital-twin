# Report figure captions and layout options

Model/data version v0.2; editorial handoff v0.3 (2026-11-03). Original files and release hashes are unchanged. These captions can be copied into the English report. P=periodic; A=age; E=error only; EA=error OR age. All times/lengths are illustrative.

## Figure 1 — State accuracy and communication cost

**Caption.** Position RMSE versus total logical update-byte rate for all predeclared workpoints in the displayed conditions. The upper row uses constant-velocity motion (|Δv|=0); the lower row uses random signed velocity jumps of magnitude 2 m/s. Columns show data-loss probabilities 0, 0.1 and 0.3. Points are means over 30 paired evaluation seeds (100–129); horizontal and vertical intervals are pointwise 95% seed-bootstrap percentile intervals (10000 resamples), not simultaneous confidence bands for an optimal frontier. The lower-row RMSE axis uses a symmetric-log scale, linear below 0.1 m; the byte-rate axis is linear and retains E's zero-byte point. Overlapping workpoints are retained. Each run lasts 60 s with a 0.01 s step, exact common initialization and noiseless state/velocity observations. Data and generated ACK bytes are both charged. All 12 motion/loss conditions, including intermediate jump magnitudes, are reported in the accompanying result tables.

**Files / exact source.** `figures/v0.2/01_tradeoff.pdf` (also SVG/PNG); `tables/v0.2/figure01_data.csv`, traced to `results/v0.2/workpoint_summary.csv` and `evaluation_runs.csv`. Grid: P or A=0.25/0.5/1/2/4 s; η=0.05/0.1/0.2/0.5/1 m; EA uses all A×η combinations. C=3200 bit/s; data/ACK=32/16 B; forward/ACK extra delay=.05/.02 s; reliable ACK, stop-and-wait, no queue.

**Layout option.** Prefer a landscape-width panel spanning the available text width, with its caption below. If labels become too small, split by motion row into two 1×3 groups with their original shared scales and one legend; do not crop the x=0 point or remove a weak periodic point to improve appearance. Suggested short title: *Accuracy–cost trade-off*. Do not interpret the smaller numerical separation on the symlog axis as a linear distance.

## Figure 2 — Response to a single manoeuvre

**Caption.** Local response to a prespecified velocity change from 1 to 3 m/s at τ=4.3 s, with no data loss (loss=0). The displayed time window is 3.8–6.5 s within a total 60 s run. Panels show position, absolute position error, receiver AoI, and cumulative logical data-plus-ACK bytes since initialization. P=A=1 s and η=0.2 m; E has no age trigger. The 0.5 m line is the evaluation tolerance, not the trigger threshold. P and A coincide; E and EA have coincident position-error traces in this example, while their AoI and communication costs can differ. The vertical line marks the manoeuvre. Packets carry generation-time position and velocity and are extrapolated to the current time on receipt. This deterministic mechanism illustration uses the prespecified seed 100; its local traces are distinct from full-window run-level statistics.

**Files / exact source.** `figures/v0.2/02_maneuver.pdf` (also SVG/PNG); `results/v0.2/maneuver_{periodic,age,error,error_age}_trace.csv` and corresponding `_events.json`. C=3200 bit/s, data/ACK=32/16 B, data/ACK service=.08/.04 s, forward/ACK extra delay=.05/.02 s, reliable ACK, dt=.01 s, no measurement noise. Initial p=0 m,v=1 m/s are shared exactly and are not billed.

**Layout option.** Keep the four aligned panels at a readable width; alternatively place position/error and AoI/bytes in two aligned two-panel groups with the same 3.8–6.5 s x range. Retain E/EA and P/A in the legend even when curves overlap. Suggested short title: *Single-manoeuvre response*.

## Figure 3 — Forward- and feedback-delay slices

**Caption.** Delay sensitivity for |Δv|=2 m/s and data-loss probability 0.1, evaluated with 30 paired seeds. Columns show position RMSE, actual total logical byte rate, time above the 0.5 m error tolerance, and mean receiver AoI. The upper row varies the forward extra delay (0, 0.05, 0.2 s) while ACK extra delay is 0.02 s; the lower row varies ACK extra delay (0.02, 0.2, 0.8 s) while forward extra delay is 0.05 s. Configurations were selected using tuning seeds 0–9 under a 48 B/s mean tuning cap and then held fixed: P=1 s, A=2 s, E η=0.05 m, and EA η=0.05 m with A=4 s. Actual evaluation costs differ between policies and need not satisfy a hard cap. Intervals are pointwise 95% run-level bootstrap intervals, not simultaneous bands. Zero forward extra delay still includes the 0.08 s data service time. ACKs are reliable; increasing ACK delay changes transaction occupancy and opportunities to send, not robustness to a stale predictor at an eligible decision point. Connecting segments join measured settings and do not establish a continuous delay law.

**Files / exact source.** `figures/v0.2/03_delay_slices.pdf` (also SVG/PNG); `results/v0.2/slice_summary.csv` from `slice_runs.csv`; configuration selection from `selected_configs.json`. T=60 s,dt=.01 s; C=3200 bit/s,data/ACK32/16 B; no jitter. Both slice families include the same base setting: their base points must not be treated as independent replications.

**Layout option.** The existing 2×4 layout should not be shrunk into a narrow single-column block. Prefer two 2×2 groups (forward delay and ACK delay) with four metrics in the same order, a shared legend and explicit policy/CI labels. A report may label them Fig.3(a)/(b), or number them separately if space requires. New layout assets, if produced by the report role, must be saved outside `figures/v0.2/` and linked to the same frozen CSV. Suggested short title: *Delay sensitivity of frozen candidates*.

## Verification scope

The experiment role visually checked the three original PNGs during stage 2; the coordinator also visually checked them in its scoped review. No new PDF layout assets are created in this handoff. Independent PDF raster rendering and readability at the final manuscript size have **not** been performed by the experiment role; the report role must check the embedded figures on actual pages. Do not change this statement to “PDF checked” without rendering and inspecting it.
