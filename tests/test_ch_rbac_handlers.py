"""RBAC handler tests moved here from core's tests/engine/backends/clickhouse/test_ch_handlers.py."""

from dbwarden.engine.core import Op
from dbwarden.engine.snapshot import snapshot_diff_to_sql

from dbwarden_ch_rbac import (
    ChNamedCollectionHandler,
    ChQuotaHandler,
    ChRoleHandler,
    ChRowPolicyHandler,
    ChSettingsProfileHandler,
    ChUserHandler,
)


class TestChLowRiskRollback:
    def test_drop_named_collection_rollback_recreates_prior_state(self):
        handler = ChNamedCollectionHandler()
        stmts = handler.emit(Op(
            object_type="drop_ch_named_collection",
            upgrade_attrs={"name": "s3_creds"},
            rollback_attrs={
                "name": "s3_creds",
                "entries": {"access_key_id": "AKID"},
                "overridable": {"access_key_id": False},
            },
        ))

        assert stmts[0].upgrade_sql == "DROP NAMED COLLECTION s3_creds"
        assert "CREATE NAMED COLLECTION s3_creds AS access_key_id = 'AKID', access_key_id NOT OVERRIDABLE" == stmts[0].rollback_sql

    def test_alter_named_collection_rollback_recreates_prior_state(self):
        handler = ChNamedCollectionHandler()
        stmts = handler.emit(Op(
            object_type="alter_ch_named_collection",
            upgrade_attrs={"name": "cfg", "entries": {"k1": "v2"}, "overridable": None},
            rollback_attrs={"name": "cfg", "entries": {"k1": "v1"}, "overridable": {"k1": False}},
        ))

        assert "DROP NAMED COLLECTION cfg" in stmts[0].upgrade_sql
        assert "CREATE NAMED COLLECTION cfg AS k1 = 'v2'" in stmts[0].upgrade_sql
        assert "CREATE NAMED COLLECTION cfg AS k1 = 'v1', k1 NOT OVERRIDABLE" in stmts[0].rollback_sql

    def test_drop_settings_profile_rollback_recreates_prior_state(self):
        handler = ChSettingsProfileHandler()
        stmts = handler.emit(Op(
            object_type="drop_ch_settings_profile",
            upgrade_attrs={"name": "readonly"},
            rollback_attrs={
                "name": "readonly",
                "settings": {"readonly": 1},
                "to_roles": ["analyst"],
            },
        ))

        assert stmts[0].upgrade_sql == "DROP SETTINGS PROFILE IF EXISTS readonly;"
        assert stmts[0].rollback_sql == "CREATE SETTINGS PROFILE readonly SETTINGS readonly=1 TO analyst;"

    def test_alter_settings_profile_rollback_restores_prior_state(self):
        handler = ChSettingsProfileHandler()
        stmts = handler.emit(Op(
            object_type="alter_ch_settings_profile",
            upgrade_attrs={"name": "readonly", "settings": {"readonly": 2}, "to_roles": ["admin"]},
            rollback_attrs={"name": "readonly", "settings": {"readonly": 1}, "to_roles": ["analyst"]},
        ))

        assert stmts[0].upgrade_sql == "ALTER SETTINGS PROFILE readonly SETTINGS readonly=2 TO admin;"
        assert stmts[0].rollback_sql == "ALTER SETTINGS PROFILE readonly SETTINGS readonly=1 TO analyst;"

    def test_drop_row_policy_rollback_recreates_prior_state(self):
        handler = ChRowPolicyHandler()
        stmts = handler.emit(Op(
            object_type="drop_ch_row_policy",
            upgrade_attrs={"name": "tenant_policy", "table": "events"},
            rollback_attrs={
                "name": "tenant_policy",
                "table": "events",
                "using": "tenant_id = 1",
                "to_roles": ["app"],
                "permissive": False,
            },
        ))

        assert stmts[0].upgrade_sql == "DROP ROW POLICY IF EXISTS tenant_policy ON events;"
        assert stmts[0].rollback_sql == "CREATE ROW POLICY IF NOT EXISTS tenant_policy ON events FOR SELECT USING tenant_id = 1 AS RESTRICTIVE TO app;"

    def test_alter_row_policy_rollback_restores_prior_state(self):
        handler = ChRowPolicyHandler()
        stmts = handler.emit(Op(
            object_type="alter_ch_row_policy",
            upgrade_attrs={"name": "tenant_policy", "table": "events", "using": "tenant_id = 2", "to_roles": ["admin"], "permissive": True},
            rollback_attrs={"name": "tenant_policy", "table": "events", "using": "tenant_id = 1", "to_roles": ["app"], "permissive": False},
        ))

        assert "DROP ROW POLICY IF EXISTS tenant_policy ON events;" in stmts[0].upgrade_sql
        assert "CREATE ROW POLICY IF NOT EXISTS tenant_policy ON events FOR SELECT USING tenant_id = 2 AS PERMISSIVE TO admin;" in stmts[0].upgrade_sql
        assert "CREATE ROW POLICY IF NOT EXISTS tenant_policy ON events FOR SELECT USING tenant_id = 1 AS RESTRICTIVE TO app;" in stmts[0].rollback_sql

    def test_low_risk_ch_paths_pass_strict_contract_with_prior_state(self):
        _up_sql, rb_sql, _changes = snapshot_diff_to_sql(
            [
                {
                    "type": "drop_ch_named_collection",
                    "name": "cfg",
                    "__rollback_attrs": {"name": "cfg", "entries": {"k1": "v1"}},
                },
                {
                    "type": "drop_ch_settings_profile",
                    "name": "readonly",
                    "__rollback_attrs": {"name": "readonly", "settings": {"readonly": 1}, "to_roles": ["analyst"]},
                },
                {
                    "type": "drop_ch_row_policy",
                    "name": "tenant_policy",
                    "table": "events",
                    "__rollback_attrs": {"name": "tenant_policy", "table": "events", "using": "tenant_id = 1", "to_roles": ["app"]},
                },
            ],
            [],
            db_name="clickhouse",
            enforce_rollback_contract=True,
        )

        assert "CREATE NAMED COLLECTION cfg AS k1 = 'v1'" in rb_sql
        assert "CREATE SETTINGS PROFILE readonly SETTINGS readonly=1 TO analyst;" in rb_sql
        assert "CREATE ROW POLICY IF NOT EXISTS tenant_policy ON events" in rb_sql


class TestChDeepRbacRollback:
    def test_drop_user_rollback_recreates_prior_state(self):
        handler = ChUserHandler()
        stmts = handler.emit(Op(
            object_type="drop_ch_user",
            upgrade_attrs={"name": "svc"},
            rollback_attrs={
                "name": "svc",
                "auth": "no_password",
                "host": "ANY",
                "roles": ["reader"],
                "default_roles": ["reader"],
                "settings_profile": "readonly",
            },
        ))

        assert stmts[0].upgrade_sql == "DROP USER IF EXISTS svc;"
        assert stmts[0].rollback_sql == "CREATE USER IF NOT EXISTS svc IDENTIFIED WITH no_password HOST ANY TO reader DEFAULT ROLE reader SETTINGS PROFILE readonly;"

    def test_alter_user_rollback_restores_prior_state(self):
        handler = ChUserHandler()
        stmts = handler.emit(Op(
            object_type="alter_ch_user",
            upgrade_attrs={"name": "svc", "auth": "no_password", "host": "LOCAL", "roles": ["admin"]},
            rollback_attrs={"name": "svc", "auth": "no_password", "host": "ANY", "roles": ["reader"]},
        ))

        assert "DROP USER IF EXISTS svc;" in stmts[0].upgrade_sql
        assert "CREATE USER IF NOT EXISTS svc IDENTIFIED WITH no_password HOST LOCAL TO admin;" in stmts[0].upgrade_sql
        assert "CREATE USER IF NOT EXISTS svc IDENTIFIED WITH no_password HOST ANY TO reader;" in stmts[0].rollback_sql

    def test_drop_role_rollback_recreates_prior_settings(self):
        handler = ChRoleHandler()
        stmts = handler.emit(Op(
            object_type="drop_ch_role",
            upgrade_attrs={"name": "reader"},
            rollback_attrs={"name": "reader", "settings": {"readonly": 1}},
        ))

        assert stmts[0].upgrade_sql == "DROP ROLE IF EXISTS reader;"
        assert stmts[0].rollback_sql == "CREATE ROLE IF NOT EXISTS reader SETTINGS readonly=1;"

    def test_alter_role_rollback_restores_prior_settings(self):
        handler = ChRoleHandler()
        stmts = handler.emit(Op(
            object_type="alter_ch_role",
            upgrade_attrs={"name": "reader", "settings": {"readonly": 2}},
            rollback_attrs={"name": "reader", "settings": {"readonly": 1}},
        ))

        assert "CREATE ROLE IF NOT EXISTS reader SETTINGS readonly=2;" in stmts[0].upgrade_sql
        assert "CREATE ROLE IF NOT EXISTS reader SETTINGS readonly=1;" in stmts[0].rollback_sql

    def test_drop_quota_rollback_recreates_prior_state(self):
        handler = ChQuotaHandler()
        stmts = handler.emit(Op(
            object_type="drop_ch_quota",
            upgrade_attrs={"name": "api_quota"},
            rollback_attrs={
                "name": "api_quota",
                "interval": "1 HOUR",
                "limits": {"queries": 1000},
                "to_roles": ["reader"],
            },
        ))

        assert stmts[0].upgrade_sql == "DROP QUOTA IF EXISTS api_quota;"
        assert stmts[0].rollback_sql == "CREATE QUOTA IF NOT EXISTS api_quota FOR INTERVAL 1 HOUR queries = 1000 TO reader;"

    def test_alter_quota_rollback_restores_prior_state(self):
        handler = ChQuotaHandler()
        stmts = handler.emit(Op(
            object_type="alter_ch_quota",
            upgrade_attrs={"name": "api_quota", "interval": "1 HOUR", "limits": {"queries": 2000}, "to_roles": ["admin"]},
            rollback_attrs={"name": "api_quota", "interval": "1 HOUR", "limits": {"queries": 1000}, "to_roles": ["reader"]},
        ))

        assert "CREATE QUOTA IF NOT EXISTS api_quota FOR INTERVAL 1 HOUR queries = 2000 TO admin;" in stmts[0].upgrade_sql
        assert "CREATE QUOTA IF NOT EXISTS api_quota FOR INTERVAL 1 HOUR queries = 1000 TO reader;" in stmts[0].rollback_sql

    def test_deep_ch_rbac_paths_pass_strict_contract_with_prior_state(self):
        _up_sql, rb_sql, _changes = snapshot_diff_to_sql(
            [
                {
                    "type": "drop_ch_user",
                    "name": "svc",
                    "__rollback_attrs": {"name": "svc", "auth": "no_password", "host": "ANY", "roles": ["reader"]},
                },
                {
                    "type": "drop_ch_role",
                    "name": "reader",
                    "__rollback_attrs": {"name": "reader", "settings": {"readonly": 1}},
                },
                {
                    "type": "drop_ch_quota",
                    "name": "api_quota",
                    "__rollback_attrs": {"name": "api_quota", "interval": "1 HOUR", "limits": {"queries": 1000}, "to_roles": ["reader"]},
                },
            ],
            [],
            db_name="clickhouse",
            enforce_rollback_contract=True,
        )

        assert "CREATE USER IF NOT EXISTS svc IDENTIFIED WITH no_password HOST ANY TO reader;" in rb_sql
        assert "CREATE ROLE IF NOT EXISTS reader SETTINGS readonly=1;" in rb_sql
        assert "CREATE QUOTA IF NOT EXISTS api_quota FOR INTERVAL 1 HOUR queries = 1000 TO reader;" in rb_sql


