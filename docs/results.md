# Historical local baseline results

Preserved baseline; current maintenance results are in [refresh-results-20260907.md](refresh-results-20260907.md).

Execution date: 2026-09-07T21:43:34Z. 9 focused unit/regression tests passed, followed by the real integration campaign. See [validation log](../evidence/local/validation.log) and [manifest](../evidence/local/manifest.json).

CPU: 13th Gen Intel(R) Core(TM) i9-13900K. Kernel: 7.0.0-29-generic. All results are author-operated local measurements; cloud CI is a separate reproducibility check.

54 matrix executions; 36 control/repaired passes; 9 expected mutation failures. Automated reduction retains failure at 1×1×1. Five executor fault categories remain explicitly non-success. UBSan covers numerical boundary shapes.

Paired 128³ kernel study: repaired/control median ratio **0.3779**, 95% bootstrap interval [0.3452, 0.4290], 20 pairs, decision **improvement** under a 5% practical threshold. This is an operator microbenchmark, not HTTP or GPU speedup.

[Correctness records](../evidence/local/correctness.jsonl) · [All paired samples](../evidence/local/performance.jsonl) · [Reduction](../evidence/local/reduction.json) · [Faults](../evidence/local/faults.json) · [Generated assembly](../evidence/local/disassembly.txt)
