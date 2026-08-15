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

__version__ = "0.2.0"

# The dbwarden plugin contract this package targets. Core refuses to load a
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


CONFIG_KEYS = (
    "ch_named_collections",
    "ch_roles",
    "ch_users",
    "ch_row_policies",
    "ch_quotas",
    "ch_settings_profiles",
    "ch_grants",
)


def setup(registrar) -> None:
    for handler_class in HANDLER_CLASSES:
        registrar.register_object_handler(handler_class())
    # Declares the database_config(...) keys this plugin consumes so core can
    # reject them with an install hint when the plugin is absent. Guarded so the
    # plugin still loads against cores predating the config-key registry.
    register_config_key = getattr(registrar, "register_config_key", None)
    if register_config_key is not None:
        register_config_key(*CONFIG_KEYS)


__all__ = [
    "CONFIG_KEYS",
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
