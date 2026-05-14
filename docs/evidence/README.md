# Evidence Policy

Raw transaction logs are local runtime artifacts and live under `logs/`.
They are gitignored and should not be committed.

Selected evidence can be copied here manually as sanitized snippets.

External app exports may also be summarized here when they are used only as
sanity evidence. Do not commit full app exports; include a small markdown or
JSON summary with the extracted values and status decision.

Sanitized evidence should contain only:

- profile id;
- probe id;
- menu/protocol context when useful;
- TX/RX hex;
- validation reasons;
- decoded values;
- status decision.

Do not include:

- local absolute paths;
- serial adapter identifiers beyond generic port context;
- large raw dumps;
- unrelated CLI output;
- personal machine data.
