# EEEN3008J Topic 35: Digital-twin synchronization using state error and age

This repository contains the Python simulation and reproducibility materials for the EEEN3008J Wireless Communications project. A receiver extrapolates the position of a one-dimensional moving object from the most recently accepted position and velocity. The experiment compares periodic, age-triggered, error-triggered, and error-or-age updates with finite-rate, stop-and-wait delivery.

| Material | Location |
| --- | --- |
| Simulation and policy logic | [simulator_v02.py](experiments/simulator_v02.py) |
| Model, assumptions, and parameters | [Experiment specification](experiments/experiment_spec_v02.md) and [configuration](experiments/configs/formal_v02.json) |
| Run-level data and statistical summaries | [Frozen v0.2 results](experiments/results/v0.2/) |
| Figures and captions | [Experiment figures](experiments/figures/v0.2/) and [figure captions](experiments/figure_captions_v03.md) |
| Report tables and matched-threshold comparisons | [Results table](experiments/report_results_table.md) and [E/EA comparison](experiments/ablation_E_EA_v03.md) |

## Verify the saved results

The verified experiment environment was Windows with Python 3.10.0, NumPy 2.2.6, and Matplotlib 3.10.9. From the repository root, use PowerShell with Python 3.10 available through the Python launcher:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r experiments/requirements_analysis.txt
.\.venv\Scripts\python.exe -X utf8 experiments/verify_report_handoff.py
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s experiments -v
```

The verifier checks the 51 frozen artifacts and recalculates selected results from the saved CSVs. It writes a verification summary to `experiments/results/report_v03/handoff_validation.json`. The test suite contains 18 tests.

The saved outputs include 4,800 tuning runs and 14,400 evaluation runs across 12 synthetic motion and loss conditions. To rerun the full experiment, use a separate checkout because the scripts write the corresponding result files.

```powershell
.\.venv\Scripts\python.exe -X utf8 experiments/scan_v02.py --workers 4
.\.venv\Scripts\python.exe -X utf8 experiments/analyze_results.py
.\.venv\Scripts\python.exe -X utf8 experiments/supplement.py
.\.venv\Scripts\python.exe -X utf8 experiments/plot_results.py
```
