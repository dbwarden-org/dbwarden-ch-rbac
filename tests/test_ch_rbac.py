def test_import():
    from dbwarden_ch_rbac import setup
    assert callable(setup)
