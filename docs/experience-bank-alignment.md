# Experience Bank implementation map

Result provenance: owner-confirmed separate cloud-hosted test results. The README reproduces the current selected bullets. Commands below exercise this checkout; new outcomes must be recorded separately from those supplied results.

| Result | Implementation and regression evidence | Reproduce | Scope / source difference |
|---|---|---|---|
| 1 | [src/gemm.cpp](../src/gemm.cpp) · [scripts/validate.py](../scripts/validate.py) | `make verify` | Four-element K-tail mutant; control, repair and candidate outcomes remain separate. |
| 2 | [qualify.py](../qualify.py) · [tests/test_qualification.py](../tests/test_qualification.py) | `make test` | Only independently confirmed wrong answers satisfy reduction; infrastructure failures do not. |
| 3 | [qualify.py](../qualify.py) · [tests/test_process_lifecycle.py](../tests/test_process_lifecycle.py) | `make test` | Strict protocol and numeric validation rejects bool/float version aliases. |
| 4 | [qualify.py](../qualify.py) · [tests/test_process_lifecycle.py](../tests/test_process_lifecycle.py) | `make test` | New worker session, group termination and direct-child reaping; escaped descendants excluded. |
| 5 | [qualify.py](../qualify.py) · [scripts/validate.py](../scripts/validate.py) | `make verify` | New local timings remain separate from the supplied cloud 1.02 [0.98,1.06] result. |

## Measurement boundaries

- 54 executions are 6 shapes × 3 seeds × 3 variants; the 9 mutant passes on K-divisible shapes are positive controls (54 − 36 − 9 = 9), and expected mutant failures must not be reported as test failures.
- The targeted regression makes the first three shapes' tail contributions fixed nonzero so the known K-tail error is observable; this is not unbiased random coverage, and K-divisible shapes plus zero-input positive controls are retained so the tool cannot mark every candidate bad.
- The oracle is independent (triple loop with arbitrary-precision integers, checked by a 1×1 hand calculation and a zero matrix), but a reference can still be wrong; re-executing reference and candidate at each reduction step is what keeps the predicate honest — infrastructure or parse failures cannot become counterexamples.
- Process-group cleanup covers cooperative descendants that did not escape the session/process group; a malicious setsid escape needs stronger isolation, which this project does not promise.
- 20 paired kernel samples on a single fixed CPU core measure kernel-only timing: no HTTP throughput, production workload, GPU behavior or endpoint speedup claim, and the geomean 1.02 point estimate is not significant because the 95% CI [0.98, 1.06] includes 1.
- UBSan runs are deliberately kept out of the performance sample; all qualification work is local CPU, not CUDA/GPU execution or a customer compiler defect.

## Local verification

See `docs/alignment-verification.json` for commands and outcomes from this checkout. Supplied cloud numbers, historical checked-in artifacts and new local checks are separate evidence sets. A skipped dependency test is not a pass.
