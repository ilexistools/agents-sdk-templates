---
name: catalog-extend-platform
description: Change the template's platform rather than an item, such as adding a model provider, a platform-wide setting, a catalog manifest field, an API endpoint, a dashboard feature, a channel or the security layer, while keeping existing items, tests and docs working. Use when a request cannot be met inside app/agents or app/tools, or explicitly targets app/catalog*, app/settings.py, app/security.py, app/orchestration or the dashboard.
---

# Extend the platform

Read `docs/architecture.md` first. Platform changes affect every project built
from the template, so they must stay backward compatible, documented and tested.
Prefer the smallest change; if the need is specific to one item, solve it inside
the item instead (`catalog-create-item`).

## Common changes

### Add a model provider
1. If it has an OpenAI-compatible endpoint, add one `Provider(...)` to `PROVIDERS`
   in `app/orchestration/providers.py` (id, label, base URL, key setting or
   `base_url_env`, `key_optional` for local servers, 1–3 example models).
2. Add its key (commented) to `env-example`.
3. Add it to the provider tables in `README.md` and `docs/catalog-standards.md`.
4. Settings and the dashboard pick it up automatically; `test_catalog` covers parsing.
Without a compatible endpoint, do not add provider branches to handlers: discuss a
dedicated wrapper first.

### Add a platform-wide setting
Only for settings used by the platform itself (item settings go in `requires`).
Add it to `FIELDS` in `app/settings.py` (key, group, label, help, `secret`,
`default`, `choices`), validate it in `validate()` if it has a format, document it
in the README configuration table and `env-example`, and test that an invalid
value is rejected.

### Add a manifest field
Add it to `Item` in `app/catalog.py` with a default (existing items must keep
loading), enforce rules in `check()` if needed, show it in `catalog.html` if it
matters to users, update both templates in `app/templates/catalog/`, the table in
`docs/catalog-standards.md` section 4, and the reference items.

### Add an API endpoint or dashboard feature
Endpoints go in `app/catalog_api.py` under `/api/...`; they are protected by the
token middleware automatically. Return JSON, map `ValueError` to 422 and
`Unavailable` to 409, never echo secrets. Dashboard code stays dependency-free
(vanilla JS; colors only through the CSS variables, which are defined for the light
theme, `:root[data-theme=dark]` and the system dark preference; English text; accessible
labels). Verify in a browser at desktop and mobile widths.

## Invariants

- English everywhere in the catalog, code and UI.
- Secrets are write-only: no endpoint returns a key value.
- `python -m app serve` keeps refusing public hosts without `CATALOG_TOKEN`;
  `/health` stays the only public route.
- Every channel executes through `catalog.execute`.
- All tests run offline; new behavior gets a test in `app/tests/`.

## Finish

```bash
uv run --locked python -m unittest discover -s app/tests -v
uv run --locked python -m app catalog check
git diff --check
```

Update `CHANGELOG.md` (section "Unreleased"), `README.md`, `docs/architecture.md`
and any skill whose instructions the change affects. Call out behavior changes.
