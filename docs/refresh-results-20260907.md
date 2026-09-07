# Maintenance validation — 2026-09-07

**12 focused tests passed**, followed by the real integration campaign. [Raw log](../evidence/refresh-20260907/validation.log) · [manifest](../evidence/refresh-20260907/manifest.json).

Run: 2026-09-07T22:42:06Z; Python 3.14.4, 13th Gen Intel(R) Core(TM) i9-13900K, Linux 7.0.0-29-generic. Single author-operated Linux CPU host. Hosted CI execution is separate.

54 matrix executions: 36 control/repaired passes, 9 expected mutation failures. Independent exact integer oracle and UBSan campaign passed. New tests reject boolean protocol and invalid/nonfinite output, kill ordinary child/grandchild process groups at timeout, and retain partial diagnostics.

Existing 128³ comparison, 20 randomized pairs: repaired/control median ratio 0.3205, 95% bootstrap interval [0.27390309960861425, 0.4124051564429525], decision `improvement` under a 5% practical threshold. This compares kernels, not old/new lifecycle code; no maintenance speedup is claimed.

[All correctness records](../evidence/refresh-20260907/correctness.jsonl) · [timings](../evidence/refresh-20260907/performance.jsonl) · [summary](../evidence/refresh-20260907/summary.json)
