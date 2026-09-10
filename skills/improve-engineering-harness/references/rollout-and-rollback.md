# Rollout and rollback

Harness changes can have large blast radius because they affect future agent decisions.

Use staged rollout when changing:

- Skill descriptions/routing;
- shared AGENTS instructions;
- safety or permission gates;
- release/test policy;
- organization-wide tools;
- widely reused schemas/interfaces.

Record:

- previous artifact/version;
- new artifact/version;
- affected repositories/users;
- evaluation evidence;
- rollback trigger;
- rollback procedure;
- observation period if relevant.

Rollback when the change increases material false blocks, routes tasks incorrectly, weakens safety, or creates new repeated failure patterns.

Do not defend a bad harness abstraction because agents have already adapted to it.
