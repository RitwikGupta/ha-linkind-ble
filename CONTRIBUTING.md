# Contributing

Use Python 3.14 and the pinned HA test environment:

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements_test.txt
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/pytest --cov --cov-report=term-missing --cov-fail-under=95
```

Tests load the real Home Assistant config flow and event platform while mocking
the radio boundary. They do not connect to a real home, button, or proxy. Parser
tests exercise malformed frames, repeated bursts, counter wrap, full-payload
identity, quiet-period expiry, independent devices, and the cache bound.

## Protocol contributions

Explain exactly what you observed and separate observations from interpretations.
Report the model printed on the button, relevant hardware/firmware information,
receiver type, test sequence, timing, distinct frame count, and unexpected events.
For gesture research, test each gesture in a separate labeled trial with at least
15 seconds of silence between trials. Do not infer gesture labels from a mixed
or unlabeled capture.

Keep raw captures private initially. Filter to your own device, remove unrelated
Bluetooth traffic and identifiers, and replace addresses with obvious placeholders
such as `AA:BB:CC:DD:EE:01`. Payloads may themselves encode device-specific
information; use synthetic fixtures for public regression tests unless the exact
bytes are necessary and you have reviewed them for disclosure.

Do not include API keys, Wi-Fi credentials, HA backups, receiver addresses, or
home screenshots in issues or commits. Integration diagnostics intentionally
include only the model and aggregate decoder counters.

## Releases

Keep `manifest.json` and `CHANGELOG.md` aligned. Run lint, tests, hassfest, and HACS
validation before tagging a release. Mark releases experimental while gesture
semantics and broader hardware compatibility remain unverified. Do not claim
Home Assistant core support or a HACS default-catalog listing.
