from __future__ import annotations

from dbwarden_ch_rbac.handlers import (
    ChGrantHandler,
    ChNamedCollectionHandler,
    ChQuotaHandler,
    ChRoleHandler,
    ChRowPolicyHandler,
    ChSettingsProfileHandler,
    ChUserHandler,
)

__version__ = "0.1.0"

# The DBWarden plugin contract this package targets. Core refuses to load a
# plugin declaring a version it does not provide, so a mismatched pairing fails
# at load with one clear message instead of somewhere inside a migration.
DBWARDEN_PLUGIN_API = 1

# Registration order mirrors ClickHouse's RBAC dependency order: profiles are
# referenced by roles and users, roles are granted to users, and grants/policies
# reference every principal above them.
HANDLER_CLASSES = (
    ChSettingsProfileHandler,
    ChRoleHandler,
    ChUserHandler,
    ChQuotaHandler,
    ChRowPolicyHandler,
    ChNamedCollectionHandler,
    ChGrantHandler,
)


def setup(registrar) -> None:
    for handler_class in HANDLER_CLASSES:
        registrar.register_object_handler(handler_class())


__all__ = [
    "ChGrantHandler",
    "ChNamedCollectionHandler",
    "ChQuotaHandler",
    "ChRoleHandler",
    "ChRowPolicyHandler",
    "ChSettingsProfileHandler",
    "ChUserHandler",
    "HANDLER_CLASSES",
    "setup",
]
