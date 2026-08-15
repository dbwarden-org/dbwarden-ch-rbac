# dbwarden-ch-rbac

[![Python](https://img.shields.io/badge/Python-3.12.7%2B-3776AB?logo=python&logoColor=white&style=for-the-badge)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/dbwarden-ch-rbac?logo=pypi&logoColor=white&style=for-the-badge)](https://pypi.org/project/dbwarden-ch-rbac/)
[![CI](https://img.shields.io/github/actions/workflow/status/dbwarden-org/dbwarden-ch-rbac/test.yml?logo=github&logoColor=white&style=for-the-badge)](https://github.com/dbwarden-org/dbwarden-ch-rbac/actions/workflows/test.yml)

ClickHouse RBAC object handlers for [dbwarden](https://github.com/dbwarden-org/dbwarden).

Teaches dbwarden's schema diff to manage ClickHouse access control the same way it manages tables: extracted from a live snapshot, diffed against your models, and emitted as reversible migration SQL.

## Object types

| Object type | Manages |
|---|---|
| `ch_settings_profile` | `CREATE/ALTER/DROP SETTINGS PROFILE` |
| `ch_role` | `CREATE/ALTER/DROP ROLE` |
| `ch_user` | `CREATE/ALTER/DROP USER`, including auth, host, and default roles |
| `ch_quota` | `CREATE/ALTER/DROP QUOTA` |
| `ch_row_policy` | `CREATE/ALTER/DROP ROW POLICY` |
| `ch_named_collection` | `CREATE/ALTER/DROP NAMED COLLECTION`, with secret values redacted in snapshots |
| `ch_grant` | `GRANT` / `REVOKE` |

Handlers register in ClickHouse's RBAC dependency order (profiles, then roles, then users, then everything that references them) so a single migration applies cleanly in one pass.

## Installation

```bash
dbwarden plugin add dbwarden-ch-rbac
```

## Trust tier

This is an **official** dbwarden plugin. Its distribution name is classified before any of its code is imported, and `dbwarden plugin add` verifies the PyPI Trusted-Publishing attestation (PEP 740) against `dbwarden-org/dbwarden-ch-rbac` before installing. It loads automatically once installed, with no `dbwarden plugin trust` step.

## Development

```bash
uv venv && uv pip install -e . -e ../dbwarden pytest
pytest -q
```

The `tests/test_conformance.py` suite runs dbwarden's shared conformance harness (`dbwarden.plugin_conformance`): entry point resolution, no import-time side effects, hook signatures, public-API-only imports, and idempotent `setup()`.

## License

MIT
