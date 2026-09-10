# Prompt versus tool

A prompt is appropriate for judgment. A tool is appropriate for repeatable truth.

Prefer a deterministic tool when the task is primarily:

- parsing known formats;
- graph reachability or dependency analysis;
- schema validation;
- fingerprinting/version binding;
- exact comparison/diffing;
- invariant checking;
- permission/environment preflight;
- arithmetic/threshold evaluation;
- enumerating repository structure;
- converting stable inputs into stable outputs.

Prefer Skill prose when the task requires:

- choosing among genuine architectural tradeoffs;
- deciding which evidence is materially relevant;
- formulating causal hypotheses;
- selecting experiments under uncertainty;
- adjudicating severity where context matters;
- designing boundaries/contracts from ambiguous requirements.

A common hybrid is best: Skill chooses **what** must be proven; scripts determine **whether** mechanical prerequisites hold.

If the agent repeatedly receives the same instruction and still fails, ask whether the instruction should become executable.
