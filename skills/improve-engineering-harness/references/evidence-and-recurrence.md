# Evidence and recurrence

Improve the harness from observed behavior, not speculative discomfort.

## Ordinary threshold

For normal quality/friction issues, prefer one of:

- two or more independent cases showing the same mechanism;
- one deterministic reproducer that reliably fails;
- one broad regression demonstrated across representative cases.

## Single-case exception

One case can justify immediate action when it reveals:

- a safety or permission escape;
- data corruption risk;
- production mutation risk;
- a structurally deterministic defect in a shared checker;
- a high-blast-radius routing or evidence-binding defect.

## Evidence quality

Strong evidence includes minimized fixtures, deterministic command outputs, exact tool/API behavior, bound execution records, and reproducible repository states.

Weak evidence includes vague dissatisfaction, one malformed user prompt, remembered behavior without artifacts, and reasoning that starts with the desired fix.

## Independence

Two examples copied from the same root cause are not necessarily two independent signals. Record whether cases differ in task, workflow, agent run, or environment.

## Minimize sensitive data

Store the smallest artifact that reproduces the harness behavior. Prefer synthetic/minimized fixtures over real production payloads.
