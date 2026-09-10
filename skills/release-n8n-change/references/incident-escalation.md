# Incident escalation

After publication, the release skill may verify, rollback, or stop. It must not become an emergency debugger.

Escalate to `debug-n8n-workflow` when:

- observed behavior is unexplained;
- rollback restored service but root cause remains unclear;
- failure does not cleanly map to a predefined rollback trigger;
- production and lab behavior diverge unexpectedly.

Preserve release artifacts and execution IDs before handoff.

If rollback cannot be confirmed, prioritize service/operator escalation over further automated changes.
