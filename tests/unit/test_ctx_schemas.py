from pathlib import Path
import json
import yaml
from jsonschema import validate

BACKLOG = Path("_ctx/backlog/backlog.yaml")
SCHEMA = Path("docs/backlog/schema/backlog.schema.json")


def test_backlog_schema():
    data = yaml.safe_load(BACKLOG.read_text())
    schema = json.loads(SCHEMA.read_text())
    validate(instance=data, schema=schema)
