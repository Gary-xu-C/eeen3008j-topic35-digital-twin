# Report result tables (v0.2 data; stage 3 extraction)

Frozen inputs only; no new simulations. n=30 paired evaluation seeds (100–129) per feasible candidate. Configurations were selected using tuning seeds 0–9. Four metrics are run-level means with pointwise 95% percentile bootstrap CI (10000 resamples, seed 20261103). These are not simultaneous bands or hard-budget comparisons.

## Representative frozen candidates

|Policy / configuration|RMSE (m), mean [95% CI]|Time above 0.5 m (s), mean [95% CI]|Total rate (B/s), mean [95% CI]|Mean AoI (s), mean [95% CI]|Over budget|
|---|---|---|---|---|---|
|P / periodic_P1_A1_E0.2|0.72319 [0.67007, 0.78590]|13.90933 [13.31199, 14.54701]|45.65333 [45.44889, 45.85778]|0.72636 [0.71206, 0.74066]|0/30|
|A / age_P1_A2_E0.2|1.32237 [1.27240, 1.36858]|25.96167 [24.78197, 27.03869]|25.12000 [24.78222, 25.45778]|1.12909 [1.12699, 1.13123]|0/30|
|E / error_P1_A1_E0.05|0.07060 [0.06494, 0.07714]|0.28000 [0.20333, 0.36667]|24.56889 [24.21333, 24.96000]|1.27390 [1.26160, 1.28698]|0/30|
|EA / error_age_P1_A4_E0.05|0.07060 [0.06494, 0.07714]|0.28000 [0.20333, 0.36667]|24.56889 [24.21333, 24.96000]|1.27390 [1.26160, 1.28698]|0/30|

Condition: |delta v|=2 m/s, loss=0.1, tuning cap=48 B/s. Data and ACK rates are separately available in the machine-readable table.

## All 12 conditions at the predeclared 48 B/s tuning cap

Each cell is **RMSE (m); actual total B/s; over-cap runs/30**. Full four-metric intervals and all budgets are in `results/report_v03/report_selected_results.csv`. This cap does not equalize actual consumption. Zero-motion repetitions check the pipeline, rather than establish a stochastic zero-error discovery. Frozen zero-motion candidates may differ because of roundoff-scale RMSE ordering; those negligible differences do not establish a physical accuracy ranking.

|Jump magnitude (m/s)|Loss|P|A|E|EA|
|---|---|---|---|---|---|
|0|0|0.00000; 11.200; 0/30|0.00000; 11.200; 0/30|0.00000; 0.000; 0/30|0.00000; 11.200; 0/30|
|0|0.1|0.00000; 10.889; 0/30|0.00000; 12.036; 0/30|0.00000; 0.000; 0/30|0.00000; 12.036; 0/30|
|0|0.3|0.00000; 20.729; 0/30|0.00000; 14.471; 0/30|0.00000; 0.000; 0/30|0.00000; 14.471; 0/30|
|0.5|0|0.12623; 47.200; 0/30|0.12623; 47.200; 0/30|0.02285; 23.191; 0/30|0.02285; 23.191; 0/30|
|0.5|0.1|0.18080; 45.653; 0/30|0.33059; 25.120; 0/30|0.03064; 25.147; 0/30|0.03064; 25.147; 0/30|
|0.5|0.3|0.38030; 42.391; 0/30|0.33526; 29.138; 0/30|0.05274; 30.089; 0/30|0.05274; 30.089; 0/30|
|1|0|0.25245; 47.200; 0/30|0.25245; 47.200; 0/30|0.03193; 23.200; 0/30|0.03193; 23.200; 0/30|
|1|0.1|0.36159; 45.653; 0/30|0.66119; 25.120; 0/30|0.04488; 24.782; 0/30|0.04488; 24.782; 0/30|
|1|0.3|0.76061; 42.391; 0/30|0.67053; 29.138; 0/30|0.08572; 29.591; 0/30|0.08855; 41.609; 0/30|
|2|0|0.50491; 47.200; 0/30|0.50491; 47.200; 0/30|0.04896; 23.200; 0/30|0.04896; 23.200; 0/30|
|2|0.1|0.72319; 45.653; 0/30|1.32237; 25.120; 0/30|0.07060; 24.569; 0/30|0.07060; 24.569; 0/30|
|2|0.3|1.52121; 42.391; 0/30|1.34106; 29.138; 0/30|0.15468; 29.342; 0/30|0.15644; 41.751; 0/30|

## Budget feasibility across all conditions

|Tuning cap (B/s)|Feasible selections / 48|Infeasible|Over-cap evaluation uses / feasible uses|
|---|---|---|---|
|24|43/48|5|34/1290|
|48|48/48|0|0/1440|
|96|48/48|0|0/1440|

An evaluation run may appear at multiple budgets; the final column counts uses, not independent trajectories. No feasible point means no point in the predeclared grid met the **mean tuning** cap; it is not a physical impossibility theorem.

## Exact lookup

For each table record, filter evaluation_runs.csv by jump, loss, point_id, and seeds 100–129. point_id encodes P/A/eta. T=60 s, dt=.01 s, epsilon=.5 m, C=3200 bit/s, data/ACK=32/16 B, forward/ACK extra delay=.05/.02 s, reliable ACK and stop-and-wait. Fees include failed data attempts and generated ACKs. The CSV retains all 144 selections, including 5 infeasible records with blank estimates (not zeros).
