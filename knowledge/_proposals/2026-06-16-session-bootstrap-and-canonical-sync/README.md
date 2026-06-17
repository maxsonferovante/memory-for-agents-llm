# Session bootstrap and canonical sync proposal package

This package records the hook and ingestion changes needed to:

- bootstrap project context into the local ingest API at session start
- re-send canonical `knowledge/` notes persistently
- capture edit-session work summaries at session stop
- remind the user that reusable outcomes can become durable knowledge
