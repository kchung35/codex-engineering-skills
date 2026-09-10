# Skill boundaries

New Skills impose routing and context costs. Treat them as architectural units.

A strong Skill has:

- a distinct user intent;
- a coherent lifecycle;
- meaningful procedural judgment;
- a clear output/handoff;
- non-overlapping activation language;
- independent usefulness.

Usually not a Skill:

- one deterministic command;
- a checklist stage inside another lifecycle;
- project-specific facts;
- an always-applicable repository invariant;
- a reference taxonomy;
- a thin wrapper around another Skill.

Place these instead:

- deterministic operation -> `scripts/` or tool;
- repository-wide invariant/routing -> `AGENTS.md`;
- conditional domain knowledge -> `references/` or project docs;
- evolving task evidence -> case ledger;
- repeated procedure inside an existing intent -> update that Skill.

When descriptions overlap, narrow nouns and verbs around **user intent**, not internal implementation terms.
