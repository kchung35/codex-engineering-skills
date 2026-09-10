# Audit record

The release record should be reconstructable without relying on chat memory.

Record:

- release ID and timestamps;
- workflow ID;
- candidate fingerprint;
- review verdict/fingerprint;
- production baseline fingerprint and active version;
- stage result and staged version ID;
- publication result and observed active version;
- verification strategy and evidence IDs;
- rollback decision/result if any;
- terminal outcome;
- residual risks.

Do not record secret values or unnecessarily sensitive payloads.
