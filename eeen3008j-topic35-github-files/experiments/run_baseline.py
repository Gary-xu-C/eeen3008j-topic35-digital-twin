"""Run a saved smoke suite, preserving traces, events, metrics and configuration."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import platform
from datetime import datetime, timezone
from simulator import Config, POLICIES, VERSION, make_trajectory, make_channel, simulate


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=root / "configs/smoke.json")
    parser.add_argument("--output", type=Path, default=root / "results/v0.1_smoke")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    if config["spec_version"] != VERSION:
        raise ValueError("spec version mismatch")
    args.output.mkdir(parents=True, exist_ok=True)
    rows = []
    for case in config["cases"]:
        c = Config(**(config["base"] | case["overrides"]))
        trajectory = make_trajectory(c, case["scenario"], jump=case.get("jump", 2))
        channel = make_channel(c)
        for policy in POLICIES:
            r = simulate(c, policy, trajectory, channel)
            stem = case["name"] + "__" + policy
            write_csv(args.output / (stem + "__trace.csv"), r["trace"])
            (args.output / (stem + "__events.json")).write_text(
                json.dumps(r["events"], indent=2), encoding="utf-8")
            rows.append(dict(case=case["name"], scenario=case["scenario"], seed=c.seed, **r["metrics"]))
    write_csv(args.output / "metrics.csv", rows)
    source_files = [Path(__file__), root / "simulator.py", root / "test_simulator.py"]
    manifest = dict(status="completed_smoke_not_formal", version=VERSION,
                    completed_at_utc=datetime.now(timezone.utc).isoformat(),
                    python=platform.python_version(), runs=len(rows), config=config,
                    source_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files})
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    for r in rows:
        print(f"{r['case']:24s} {r['policy']:10s} RMSE={r['rmse_m']:.6f} m "
              f"over={r['over_tolerance_s']:.2f} s bytes={r['total_bytes']} AoI={r['mean_aoi_s']:.4f} s")


if __name__ == "__main__":
    main()
