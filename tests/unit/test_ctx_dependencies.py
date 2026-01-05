from importlib import import_module


def test_ctx_dependencies_import():
    for module in ("ruamel.yaml", "yaml", "jsonschema"):
        import_module(module)
