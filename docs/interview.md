# Interview preparation / 面试准备

Target: SDET · performance qualification · developer technology.

Explain the code path and one retained failure before citing any metric. All numbers must link to the checked-in evidence and its hardware/software manifest. A GitHub CI pass demonstrates reproducibility, not production use.

可陈述：独立实现、真实本地测试、故障定位、可复现证据。不可陈述：企业客户、生产规模、未测硬件成绩、上游已合并贡献、独立用户验收。先按 README 完整复现，再练习解释每个边界和失败。

## Evidence-led talking points

- Why independent? Generated matrix entries are bounded integer numerators over eight; the oracle performs integer column dot products and divides once, whereas the worker updates double rows. Explain why exact equality is valid here and why it would be wrong to reuse this policy for arbitrary FP16 inference.
- Why nine failures? Three shapes have K not divisible by eight, repeated for three seeds. Aligned candidate cases pass, so a smoke test containing only powers of two would miss the injected defect.
- Why trust the performance claim? The repaired loop runs contiguous B/C updates, consumes the output, records assembly, keeps 20 randomized adjacent pairs and a seeded bootstrap. The measurement remains conditional on a shared, frequency-uncontrolled CPU host.
- How is a runner failure different? Timeout, process failure, cancellation and missing output have distinct records and never become successful samples. The valid comparison requires complete paired observations.

Resume wording, after reproducing: “Built a C++/Python regression qualification kit with an independent exact oracle; reproduced and minimized a K-tail mutation, verified 36 control/repaired executions, and retained 20 paired performance trials with uncertainty gating.” Do not describe the mutation as an upstream bug discovery or carry over GPU speedup numbers.
