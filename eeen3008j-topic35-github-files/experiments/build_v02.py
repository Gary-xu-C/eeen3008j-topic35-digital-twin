"""One-time, reproducible derivation of v0.2 from preserved v0.1 source."""
from pathlib import Path
p = Path(__file__).resolve().parent
s = (p/'simulator.py').read_text(encoding='utf-8')
s = s.replace('v0.1', 'v0.2').replace('VERSION = "0.1"', 'VERSION = "0.2"')
s = s.replace('("periodic", "age", "error_age")', '("periodic", "age", "error", "error_age")')
s = s.replace('def simulate(c, policy, trajectory, channel):', 'def simulate(c, policy, trajectory, channel, record=True):')
s = s.replace('events.append(dict(slot=k, time_s=k*c.dt, event=kind, **info))', 'if record:\n            events.append(dict(slot=k, time_s=k*c.dt, event=kind, **info))')
s = s.replace('    for k in range(n):\n        process(k)', '    error2 = aoi_sum = max_aoi = 0.0\n    over = eligible = 0\n    period_slots = round(c.period/c.dt)\n    for k in range(n):\n        process(k)')
start = s.index('        due = ((')
end = s.index('        # k=0', start)
s = s[:start] + '''        if not busy:
            eligible += 1
            # Validation-only invariant; trigger still uses the ACK mirror alone.
            assert rx == mirror, "receiver/mirror differ at eligible decision"
        if policy == "periodic":
            due = k % period_slots == 0
        elif policy == "age":
            due = sender_age + 1e-12 >= c.max_age
        elif policy == "error":
            due = trigger_error > c.error_threshold + 1e-12
        else:
            due = trigger_error > c.error_threshold + 1e-12 or sender_age + 1e-12 >= c.max_age
''' + s[end:]
start = s.index('        trace.append(')
end = s.index('    counts["data_inflight"]',start)
block = s[start:end]
s = s[:start] + '''        error = abs(positions[k]-estimate)
        aoi = (k-rx.generation)*c.dt
        error2 += error*error
        aoi_sum += aoi
        max_aoi = max(max_aoi, aoi)
        over += error > c.tolerance + 1e-12
        if record:
''' + ''.join('    '+line+'\n' for line in block.splitlines()) + s[end:]
s = s.replace('    error2 = sum(r["error_m"]**2 for r in trace)\n    over = sum(r["error_m"] > c.tolerance + 1e-12 for r in trace)\n','')
s = s.replace('sum(r["aoi_s"] for r in trace)/n','aoi_sum/n').replace('max(r["aoi_s"] for r in trace)','max_aoi')
s = s.replace('metrics = dict(policy=policy, **counts,', 'metrics = dict(policy=policy, eligible_decisions=eligible, decision_mismatches=0, **counts,')
(p/'simulator_v02.py').write_text(s,encoding='utf-8')
