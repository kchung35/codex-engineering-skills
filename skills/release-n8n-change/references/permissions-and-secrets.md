# Permissions and secrets

Use least privilege compatible with release and rollback.

Typical release operations need workflow read/update and publication/unpublication capability. Scope names and project-level permissions may vary by n8n version and edition; validate against the target instance rather than assuming a label is sufficient.

Store API keys only in an environment variable named by configuration. Never serialize the key into release artifacts.

Never copy credential secret values between environments during release. Workflow JSON should contain credential references, not secret material.
